from organisms.activationFunctions import softmax


class NodeGene:
    """
    a neuron in the neural network. handles activation encapsulation and Connection references. This is the
    fundamental unit of encapsulation the describes the neural network topology.
    """

    # TODO: NodeGene can only be created with
    #              input and output connections should
    #              be included in constructor to enforce
    #             initialization of primal nodes in encapsulation
    #             (extract to here)

    def __init__(self, identifier):
        self.inConnections = []
        self.outConnections = []
        self.nodeId = identifier
        self.activated = False

    def __str__(self):
        inputs = str([x.input.nodeId for x in self.inConnections])
        outputs = str([x.output.nodeId for x in self.outConnections])
        return 'Node: ' + str(self.nodeId) + '\n inputs: ' + \
               inputs + '\n outputs: ' + outputs

    def addConnection(self, connectionGene):
        """
        add a Connection reference to this Node and orient based on input or output direction.
        """
        # check if Connection exists first
        # TODO: Really ought to clean up the self loop case here..
        if self.nodeId is connectionGene.output.nodeId and self.nodeId is connectionGene.input.nodeId:
            self.inConnections.append(connectionGene)
            self.outConnections.append(connectionGene)
        elif self.nodeId is connectionGene.input.nodeId:
            self.outConnections.append(connectionGene)
        elif self.nodeId is connectionGene.output.nodeId:
            self.inConnections.append(connectionGene)
        else:  # default fallthrough error
            raise Exception(
                'ERROR: cannot connect ',
                connectionGene.input.nodeId,
                '->',
                connectionGene.output.nodeId,
                ' with ',
                self.nodeId)

    def removeConnection(self, connectionGene):
        """
        removes an existing Connection from this Node
        """
        if self.nodeId is connectionGene.input.nodeId and \
                self.nodeId is connectionGene.output.nodeId:
            self.outConnections.remove(connectionGene)
            self.inConnections.remove(connectionGene)

        elif self.nodeId is connectionGene.input.nodeId:
            self.outConnections.remove(connectionGene)

        elif self.nodeId is connectionGene.output.nodeId:
            self.inConnections.remove(connectionGene)

        else:  # default fallthrough error
            raise Exception('ERROR: cannot delete ',
                            connectionGene, ' from ', self)

    def alignNodeGene(self, connection):
        """
        determines if the primal Node representation of this Node can be created by splitting the given Connection
        """
        if self.outConnections[0].output.nodeId == connection.output.nodeId and \
                self.inConnections[0].input.nodeId == connection.input.nodeId:
            return True
        else:
            return False

    # @DEPRECATED
    # def comparePrimals(self, otherNodes):
    #     '''
    #     compares this primal Node against all primal nodes in list, used for chromosome alignment operations.
    #     '''
    #     return any([self.comparePrimal(x) for x in otherNodes])

    # def comparePrimal(self, otherNode):
    #     '''
    #     compares primal representation of this Node against another primal Node representation,
    #     used for chromosome alignment operations.
    #     '''
    #     if self.outConnections[0].output.nodeId == otherNode.outConnections[0].output.nodeId and \
    #        self.inConnections[0].input.nodeId == otherNode.inConnections[0].input.nodeId:
    #         return True
    #     else:
    #         return False

    def getUnreadyConnections(self):
        """
        returns all incoming connections at this Node that don't have a signal
        (not considering loop connections)
        """
        incs = [x for x in self.inConnections if x.disabled is False]

        if any([x.signal is None and x.loop is False for x in incs]):
            blockages = [
                x for x in self.inConnections if x.signal is None and
                x.loop is False]
            return blockages
        else:
            raise Exception(
                "unready Node with no unready incoming connections")

    def activate(self, signal):
        """
        activate this neuron:
        1. matrix multiply incoming Connection weights and signals
        2. Reimann sum the results of 1
        3. call activation function for the result of 2
        4. copy result of 3 to all output Connection's signal

        PARAMETERS:
            signal: a signal directly to the neuron indicates it is an input neuron with
                    no incoming connections

        RETURNS:
            a list of nodes that have been sent signals to their incoming connections due
            to activating this neuron
            (used for chaining forward propagation activation without knowing layer
            depth of neurons)
        """
        activeSignal = 0
        nextNodes = []
        assert self.activated is False, "@ Node {}".format(self.nodeId)

        # INPUT NODE CASE
        if signal is not None and signal is not False:
            for inc in self.inConnections:
                # passively accept loop signals to input
                if inc.signal is not None and inc.disabled is False:
                    activeSignal += inc.signal
            activeSignal = softmax(activeSignal + signal)

            for outc in [
                    x for x in self.outConnections if x.disabled is False]:
                outc.signal = activeSignal
                if outc.output not in nextNodes and outc.output.activated is False:
                    nextNodes.append(outc.output)
            self.activated = True

        # OUTPUT NODE CASE
        # passing False gives a psuedo activation for copying/harvesting signals
        # at output Nodes
        elif signal is False:
            incs = [x for x in self.inConnections if x.disabled is False]
            if any([x.signal is None and x.loop is False for x in incs]):
                # persist this Node to next step due to skip Connection
                # for inc in incs:
                # if inc.signal is None and inc.loop is False:
                # print('awaiting a skip Connection or stuck in recurrence.. {} -> {}'.format(
                #     inc.input.nodeId, inc.output.nodeId))
                return [self]
            else:
                for inc in [x for x in incs if x.signal is not None]:
                    activeSignal += inc.signal * inc.weight
                    # inc.signal = None

                activeSignal = softmax(activeSignal)

                for outc in [
                        x for x in self.outConnections if x.disabled is False]:
                    outc.signal = activeSignal
                self.activated = True
                # TODO: leaves hanging Node connections that never get activated
                # need to handle propagating but graph is functional

        # HIDDEN NODE CASE
        else:
            incs = [x for x in self.inConnections if x.disabled is False]
            if any([x.signal is None and x.loop is False for x in incs]):
                # persist this Node to next step due to skip Connection
                # for inc in incs:
                # if inc.signal is None and inc.loop is False:
                # print('awaiting a skip Connection or stuck in recurrence.. {} -> {}'.format(
                #     inc.input.nodeId, inc.output.nodeId))
                return [self]
            else:
                for inc in [x for x in incs if x.signal is not None]:
                    # assert inc.signal is not None and inc.loop is False, " \
                    # @ Node {}".format(self.nodeId)
                    # if inc.signal is None:
                    #     # unready recurrent Connection
                    #     continue
                    activeSignal += inc.signal * inc.weight
                    # inc.signal = None

                activeSignal = softmax(activeSignal)

                for outc in [
                        x for x in self.outConnections if x.disabled is False]:
                    outc.signal = activeSignal
                    # dampen reverb
                    if outc.output not in nextNodes and outc.output.activated is False:
                        # if outc.output.activated:
                        #     outc.loop = True
                        nextNodes.append(outc.output)
                self.activated = True

        # TODO: trace this case (recurrence) could this also be x.loop is
        # False?
        checkNodes = []
        for node in nextNodes:
            if node.activated is False:
                checkNodes.append(node)
        return checkNodes
        # return [x for x in nextNodes if x.activated is False]
