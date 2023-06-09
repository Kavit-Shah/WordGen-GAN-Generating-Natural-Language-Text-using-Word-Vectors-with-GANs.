import tensorflow as tf


class FCLayer:
    def __init__(self, dim_in_list, dim_out, activation):
        """
        :param dim_in_list: a list of the input vector dimensionalities, one corresponding to each input to the layer
        :param dim_out: the dimensionality of the output vector
        :param activation: an activation function to apply element-wise
        """
        self.weights = []
        for dim_in in dim_in_list:
            self.weights.append(
                #tf.Variable(tf.truncated_normal([dim_in, dim_out], stddev=0.1))\
                tf.Variable(tf.contrib.layers.xavier_initializer()([dim_in, dim_out], tf.float32))
            )

        self.bias = tf.Variable(tf.fill([dim_out], 0.0))
        self.activation = activation

    def __call__(self, *inputs):
        """
        :param *inputs: input tensors of the shape [batch_size, dim_in]; must correspond to the dimensionalities that
        the layer was initialized with
        :return: tensor of the shape [batch_size, dim_out]
        """
        if len(inputs) != len(self.weights):
            raise RuntimeError("Number of inputs does not match number of inputs layer was initialized with")

        results = [tf.matmul(x, w) for x, w in zip(inputs, self.weights)]
        return self.activation(sum(results) + self.bias)


class LSTMCell:
    """
    Basic stateful LSTM cell with no peephole connections
    """

    def __init__(self, dim_in, dim_state, input_dropout, initial_state, initial_output):
        """
        :param dim_state: dimensionality of the LSTM's state vector
        :param dim_in: dimensionality of the LSTM's input vectors
        :param initial_state: a tf tensor of the shape [batch_size, dim_state] to be used as the initial state
        :param input_dropout: keep_prob for dropout on cell's input connections
        :param initial_output: a tf tensor of the shape [batch_size, dim_state] to be used as the initial 'previous output'
        """
        self.forget_gate = FCLayer([dim_in, dim_state], dim_state, tf.sigmoid)
        self.input_gate = FCLayer([dim_in, dim_state], dim_state, tf.sigmoid)
        self.candidate_creator = FCLayer([dim_in, dim_state], dim_state, tf.tanh)
        self.output_gate = FCLayer([dim_in, dim_state], dim_state, tf.sigmoid)

        self.initial_state = self.state = initial_state
        self.initial_output = self.output = initial_output

        self.input_dropout = input_dropout

    def __reset(self):
        """
        Reset the cell's internal state to point to the tf.placeholder initials
        """
        self.state = self.initial_state
        self.output = self.initial_output

    def __update(self, new_input):
        """
        Update the LSTM's internal state and return the output for that step
        :param new_input: input tensor of the shape [batch_size, dim_in]
        :return: output tensor of the shape [batch_size, dim_state]
        """
        new_input_drop = tf.nn.dropout(new_input, self.input_dropout)
        self.state *= self.forget_gate(new_input_drop, self.output)
        self.state += self.input_gate(new_input_drop, self.output) * self.candidate_creator(new_input_drop, self.output)
        self.output = tf.tanh(self.state) * self.output_gate(new_input_drop, self.output)
        return self.output, self.state

    def __call__(self, inputs):
        """
        :param inputs: a list of length sequence_length with tensors of shape [batch_size, dim_in]
        :return: a tuple of the form (outputs, states) where both are lists of tensors of length sequence_length
        and shape [batch_size, dim_state]
        """
        outputs, states = zip(*[self.__update(x) for x in inputs])
        self.__reset()
        return outputs, states
