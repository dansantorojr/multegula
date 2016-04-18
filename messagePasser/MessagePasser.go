////////////////////////////////////////////////////////////
//Multegula - MessagePasser.go
//Multicasting Message Passer for Multegula
//Armin Mahmoudi, Daniel Santoro, Garrett Miller, Lunwen He
////////////////////////////////////////////////////////////

package messagePasser

import (
	"encoding/gob"
	"errors"
	"fmt"
	"net"
	"reflect"
	"sort"
	"strconv"
	"sync"
	"time"
)

/* the size of queue: sendQueue, receivedQueue,
 * sendDelayedQueue and receiveDelayedQueue
 **/
const QUEUE_SIZE int = 100

// Node structure to hold each node's information
type Node struct {
	Name string
	IP   string
	Port int
	DNS  string
}

// required functions to implement the sort.Interface for sorting Nodes
type Nodes []Node

func (slice Nodes) Len() int {
	return len(slice)
}

func (slice Nodes) Less(i, j int) bool {
	return slice[i].Name < slice[j].Name
}

func (slice Nodes) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

/* Message structure
 * before message transported through TCP connection, it will
 * be converted to string in the format of: Source##Destination##Content##Kind
 * when message is received, it will be reconstructed
 **/
type Message struct {
	Source      string // the DNS name of sending node
	Destination string // the DNS name of receiving node
	Content     string // the Content of message
	Kind        string // the Kind of messages
	SeqNum      int
	Timestamp   []int
}

/* InitMessagePasser has to wait for all work to be done before exiting */
var wg sync.WaitGroup

/*
 * local instance holding the peer nodes.
 */
var peerNodes Nodes

/* map stores connections to each node
 * <key, value> = <name, connection>
 **/
var connections map[string]net.Conn = make(map[string]net.Conn)

func getConnectionName(connection net.Conn) (string, error) {
	for name, conn := range connections {
		if conn == connection {
			return name, nil
		}
	}
	return "Not Found", fmt.Errorf("Connection not found:%v\n", connection)
}

const multicastDestStr = "EVERYBODY"

var seqNums map[string]int = make(map[string]int)
var vectorTimeStamp []int
var localReceivedSeqNum = 0

/*
 * connection for localhost, this is the receive side,
 * the send side is stored in connections map
 **/
var localConn net.Conn

/*
 * The local node's information.
 */
var localNode Node
var localIndex int

/* the queue for messages to be sent */
var sendChannel chan Message = make(chan Message, 100)

/* the queue for received messages */
var receiveChannel chan Message = make(chan Message, 100)
var holdbackQueue []Message = []Message{}

func updateSeqNum(message *Message) {
	seqNum := seqNums[message.Destination] + 1
	seqNums[message.Destination] = seqNum
	message.SeqNum = seqNum
}

/*
 * detects if a message is the next message to be put in the receive channel
 * or not. The criteria is that the message's timestamp should have only 1 value
 * that is +1 on only 1 index of vectorTimeStamp. if there are multiple values
 * that are +1 of their respective indexes in vectorTimeStamp that means we have
 * yet not received a message that the sender of this message has received.
 *
 * Example: If we're node 0, and vectorTimeStamp = [1,2,3], and new message comes
 * in from node 1 with [1,3,4], we have missed a message from node 2 ([1,2,4])
 * that was received by node 1 before it multicasts [1,3,4]. Thus this message
 * is not ready yet, and we have to receive [1,2,4] first.
 */
func isMessageReady(message Message, sourceIndex int, localTimeStamp *[]int) bool {
	if localIndex == sourceIndex {
		if message.Timestamp[localIndex] == (localReceivedSeqNum + 1) {
			return true
		}
		return false
	}
	for i, val := range message.Timestamp {
		localValue := (*localTimeStamp)[i]
		if i == sourceIndex && i != localIndex && val != (localValue+1) {
			return false
		} else if i != sourceIndex && i != localIndex && val > localValue {
			return false
		}
	}
	return true
}

/*
 * checks to see if a message is has been received before.
 */
func messageHasBeenReceived(message Message) bool {
	/* check if message has been delivered already */
	if message.Source == localNode.Name && message.Timestamp[localIndex] <= localReceivedSeqNum {
		return true
	} else if message.Source != localNode.Name && CompareTimestampsLE(&message.Timestamp, &vectorTimeStamp) {
		return true
	}

	/* check if message is in holdbackQueue */
	for _, msg := range holdbackQueue {
		if CompareTimestampsSame(&msg.Timestamp, &message.Timestamp) {
			return true
		}
	}
	return false
}

/*
 * send TCP messages
 * @param	conn – connection to send message over
 * @param	message – message to be sent
 **/
func sendMessageTCP(nodeName string, message *Message) {
	encoder := gob.NewEncoder(connections[nodeName])
	encoder.Encode(message)
}

/*
 * receive TCP messages
 * @param	conn – the connection to use
 *
 * @return	message
 **/
func receiveMessageTCP(conn net.Conn) (Message, error) {
	dec := gob.NewDecoder(conn)
	msg := &Message{}
	err := dec.Decode(msg)
	if err != nil {
		return *msg, err
	}
	return *msg, nil
}

/*
 * basic multicasts a message to all nodes
 */
func Multicast(message *Message) {
	if message.Source == localNode.Name {
		message.Destination = multicastDestStr
		updateSeqNum(message)
		message.Timestamp = *GetNewTimestamp(&vectorTimeStamp, localIndex)
	}

	for _, node := range peerNodes {
		sendMessageTCP(node.Name, message)
	}
}

/*
 * finds a node within an array of nodes by Name
 */
func FindNodeByName(nodes []Node, name string) (int, Node, error) {
	for i, node := range nodes {
		if node.Name == name {
			return i, node, nil
		}
	}
	return -1, Node{}, errors.New("Node not found: " + name)
}

/*
 * separate nodes' DNS name into two parts based on lexicographical order
 * @param	nodes
 *			the nodes in the group
 *
 * @param	localNode
 *
 * @return	frontNodes – nodes smaller than localName
 *					latterNodes – nodes greater or equal to localName
 **/
func getFrontAndLatterNodes(nodes []Node, localNode Node) (map[string]Node, map[string]Node) {
	var frontNodes map[string]Node = make(map[string]Node)
	var latterNodes map[string]Node = make(map[string]Node)
	for _, node := range nodes {
		if node.Name < localNode.Name {
			frontNodes[node.Name] = node
		} else if node.Name > localNode.Name {
			latterNodes[node.Name] = node
		} else {
			frontNodes[node.Name] = node
			latterNodes[node.Name] = node
		}
	}
	return frontNodes, latterNodes
}

/*
 * accepts connections from other nodes and stores
 * connections into connections map, after accepting
 * all connections from all other nodes in the group,
 * this routine exits
 * @param	frontNodes
 *			map that contains all nodes with smaller Node names
 *
 * @param   localNode
 **/
func acceptConnection(frontNodes map[string]Node, localNode Node) {
	defer wg.Done()
	fmt.Println("Local Port:", strconv.Itoa(localNode.Port))
	ln, err := net.Listen("tcp", ":"+strconv.Itoa(localNode.Port))
	if err != nil {
		fmt.Println("Couldn't Start Server...")
		panic(err)
	}
	for len(frontNodes) > 0 {
		/*
		 * when a node first connects to other nodes, it will first
		 * send it's DNS name so that another node can know it's name
		 **/
		conn, _ := ln.Accept()
		msg, _ := receiveMessageTCP(conn)
		// remove the connected node from the frontNodes
		delete(frontNodes, msg.Source)
		if msg.Source == localNode.Name {
			localConn = conn
		} else {
			connections[msg.Source] = conn
			seqNums[msg.Source] = 0
		}
	}
}

/*
 * send connections to nodes with greater Names
 * and stores connections into connections map
 * @param	latterNodes
 *			map that contains all nodes with greater or equal Node names
 *
 * @param	localNode
 **/
func sendConnection(latterNodes map[string]Node, localNode Node) {
	defer wg.Done()
	for _, node := range latterNodes {
		conn, err := net.Dial("tcp", node.IP+":"+strconv.Itoa(node.Port))
		for err != nil {
			fmt.Print(".")
			time.Sleep(time.Second * 1)
			conn, err = net.Dial("tcp", node.IP+":"+strconv.Itoa(node.Port))
		}
		connections[node.Name] = conn
		seqNums[node.Name] = 0

		/* send an initial ping message to other side of the connection */
		msg := Message{localNode.Name, node.Name, "ping", "ping", 0, vectorTimeStamp}
		sendMessageTCP(node.Name, &msg)
	}
	fmt.Println()
}

/*
 * put message to receiveQueue, since the chan <- maybe blocked if the channel is full,
 * in order to not block the void receiveMessageFromConn(conn) method, we creates a new routine
 * to do this
 * @param	message
 *			the message to be put into receiveQueue
 **/
func addMessageToReceiveChannel(message Message) {
	if message.Source == localNode.Name {
		localReceivedSeqNum += 1
	} else {
		UpdateTimestamp(&vectorTimeStamp, &message.Timestamp)
	}
	receiveChannel <- message
}

/*
 * receive message from TCP connection, and put it into receivedQueue of message
 * @param	conn
 *			TCP connection
 **/
func receiveMessageFromConn(conn net.Conn) {
	for {
		msg, err := receiveMessageTCP(conn)
		if err != nil {
			name, _ := getConnectionName(conn)
			if err.Error() == "EOF" {
				fmt.Println("Lost connection to:", name)
				break
			} else {
				fmt.Printf("Error from connection:%v, Error:%v\n", name, err.Error())
				continue
			}
		}

		rule := matchReceiveRule(msg)
		/* no rule matched, put it into receivedQueue */
		if (rule == Rule{}) {
			deliverMessage(msg)
			/*
			 * there are delayed messages in receiveDelayedQueue
			 * get one and put it into receivedQueue
			 */
			for len(receiveDelayedQueue) > 0 {
				delayedMessage := <-receiveDelayedQueue
				deliverMessage(delayedMessage)
			}
		} else {
			/*
			 * there is a receive rule matched, we only need to
			 * check "delay" rule, since other rule will drop
			 * this message
			 */
			if rule.Action == "delay" {
				go putMessageToReceiveDelayedQueue(msg)
			} else {
				fmt.Printf("DROPPING Message: %+v\n", msg)
			}
		}
	}
}

/*
 * inspects a message and delivers to application (using receive channel) if
 * the message is ready. It will also check the holdbackQueue for other potential
 * messages that might be ready now.
 */
func deliverMessage(message Message) {
	if message.Destination == multicastDestStr {
		if messageHasBeenReceived(message) {
			return
		}
		sourceIndex, _, _ := FindNodeByName(peerNodes, message.Source)
		if isMessageReady(message, sourceIndex, &vectorTimeStamp) {
			addMessageToReceiveChannel(message)
			checkHoldbackQueue()
		} else {
			Push(&holdbackQueue, message)
		}
		/* Once a message has been inspected locally, check to see if it should be
		 * re-multicasted to other nodes
		 */
		if message.Source != localNode.Name {
			go Multicast(&message)
		}
	} else {
		// TODO: Handle direct messages with wrong order
		addMessageToReceiveChannel(message)
	}

}

/*
 * a recursive call that checks the holdbackQueue for any message that is ready
 * to be delivered.
 */
func checkHoldbackQueue() {
	var messageToDeliver *Message
	for i, msg := range holdbackQueue {
		sourceIndex, _, _ := FindNodeByName(peerNodes, msg.Source)
		if isMessageReady(msg, sourceIndex, &vectorTimeStamp) {
			messageToDeliver = &msg
			Delete(&holdbackQueue, i)
			break
		}
	}
	if messageToDeliver != nil {
		addMessageToReceiveChannel(*messageToDeliver)
		checkHoldbackQueue()
	}
}

/*
 * for each TCP connection, start a new receiveMessageFromConn routine to
 * receive messages sent from that connection. A constraint for this mechanism
 * is that each routine waits in a infinite loop which makes code inefficient.
 **/
func startReceiveRoutines() {
	for _, conn := range connections {
		go receiveMessageFromConn(conn)
	}
	go receiveMessageFromConn(localConn)
}

/*
 * whnever there are messages in sendChannel, send it out to TCP connection
 **/
func sendMessageToConn() {
	for {
		message := <-sendChannel
		rule := matchSendRule(message)
		/* no rules matched, send the message */
		if (rule == Rule{}) {
			sendMessageTCP(message.Destination, &message)
			/* there are delayed messages, send one */
			if len(sendDelayedQueue) > 0 {
				delayedMessage := <-sendDelayedQueue
				sendMessageTCP(delayedMessage.Destination, &delayedMessage)
			}
		} else {
			/*
			 * rule matched, only check delay rule, because other rules
			 * will drop this message
			 */
			if rule.Action == "delay" {
				go putMessageToSendDelayedQueue(message)
			}
		}
	}
}

/*
 * put message to sendChannel, since the chan <- maybe blocked if the channel is full,
 * in order to not block the void send(message Message) method, we creates a new routine
 * to do this
 * @param	message
 *			the message to be put into sendChannel
 **/
func putMessageToSendChannel(message Message) {
	sendChannel <- message
}

/*
 * send message, this is a public method
 * @param	message
 *			message to be sent
 **/
func Send(message Message) {
	if (reflect.DeepEqual(message, Message{})) {
		fmt.Println("Empty message, it is dropped!")
	} else if message.Destination == multicastDestStr {
		Multicast(&message)
	} else {
		if _, ok := connections[message.Destination]; ok {
			updateSeqNum(&message)
			go putMessageToSendChannel(message)
		} else {
			fmt.Printf("Message's destination %s is not found, it is dropped!\n", message.Destination)
		}
	}
}

/*
 * a public method that returns a message from receiveChannel
 * this method is blocking if there are no messages.
 */
func Receive() Message {
	return <-receiveChannel
}

/*
 * Prompts the user for the local Node's name
 * @return local Node's name string
 */
func getLocalName() string {
	var localName string
	fmt.Println("Who are you? (ex. armin)")
	fmt.Scanf("%s", &localName)
	if len(localName) == 0 {
		localName = "unknown" // default name
	}
	return localName
}

/*
 * print out all nodes' name
 */
func printNodesName(nodes []Node) {
	fmt.Println("Possible node names are: ")
	for _, node := range nodes {
		fmt.Printf("\t%s\n", node.Name)
	}
}

/*
 * initialize MessagePasser, this is a public method
 **/
func InitMessagePasser(nodes Nodes, localName string) {
	peerNodes = nodes
	sort.Sort(peerNodes)
	var err error
	localIndex, localNode, err = FindNodeByName(peerNodes, localName)
	if err != nil {
		panic(err)
	}

	initRules()

	// keep track of group seqNum for multicasting
	seqNums[localName] = 0
	// initialize the vectorTimeStamp
	vectorTimeStamp = make([]int, len(peerNodes))

	// separate Node names
	frontNodes, latterNodes := getFrontAndLatterNodes(peerNodes, localNode)

	//TODO: Don't wait for connections
	// wait for connections setup before proceeding
	wg.Add(2)
	// setup TCP connections
	go acceptConnection(frontNodes, localNode)
	go sendConnection(latterNodes, localNode)
	wg.Wait()

	// start routines listening on each connection to receive messages
	startReceiveRoutines()

	// start routine to send message
	go sendMessageToConn()
}
