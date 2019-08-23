from typing import Tuple, Optional
import numpy as np
import tensorflow as tf
from typing import Optional, Any
from ..agent.layers.math_embedding import MathEmbedding
from ..agent.layers.lstm_stack import LSTMStack
from ..agent.layers.math_policy_dropout import MathPolicyDropout
from ..agent.layers.bahdanau_attention import BahdanauAttention
from tensorflow.keras.layers import TimeDistributed
import os
from shutil import copyfile

from mathy.a3c.config import A3CArgs


class ActorCriticModel(tf.keras.Model):
    args: A3CArgs

    def __init__(
        self,
        args: A3CArgs,
        predictions=2,
        shared_layers=None,
        initial_state: Any = None,
    ):
        super(ActorCriticModel, self).__init__()
        self.global_step = tf.Variable(
            0, trainable=False, name="global_step", dtype=tf.int64
        )
        self.args = args
        self.predictions = predictions
        self.shared_layers = shared_layers
        self.pi_logits = tf.keras.layers.Dense(predictions, name="pi_logits")
        self.pi_sequence = TimeDistributed(
            MathPolicyDropout(self.predictions), name="pi_head"
        )
        self.lstm = LSTMStack(units=args.units, share_weights=True)
        self.value_logits = tf.keras.layers.Dense(1)
        self.embedding = MathEmbedding()
        self.attention = BahdanauAttention(self.args.units)

    def call(self, batch_features):
        inputs = batch_features
        if self.shared_layers is not None:
            for layer in self.shared_layers:
                inputs = layer(inputs)
        # Extract features into contextual inputs, sequence inputs.
        context_inputs, sequence_inputs, sequence_length = self.embedding(inputs)
        hidden_states, lstm_vectors = self.lstm(sequence_inputs, context_inputs)

        attention_context, attention_weights = self.attention(
            lstm_vectors, hidden_states
        )

        values = self.value_logits(attention_context)
        logits = self.apply_pi_mask(
            self.pi_sequence(lstm_vectors), batch_features, sequence_length
        )
        return logits, values

    def apply_pi_mask(self, logits, batch_features, sequence_length):
        """Take the policy_mask from a batch of features and multiply
        the policy logits by it to remove any invalid moves from
        selection """
        batch_mask_flat = tf.reshape(
            batch_features["policy_mask"],
            (sequence_length.shape[0], -1, self.predictions),
        )
        # Trim the logits to match the feature mask
        trim_logits = logits[:, : batch_mask_flat.shape[1], :]
        features_mask = tf.cast(batch_mask_flat, dtype=tf.float32)
        mask_logits = tf.multiply(trim_logits, features_mask)
        mask_logits = tf.where(
            tf.equal(mask_logits, tf.constant(0.0)),
            tf.fill(trim_logits.shape, -1000000.0),
            mask_logits,
        ).numpy()

        return mask_logits

    def maybe_load(self, initial_state=None, do_init=False):
        if initial_state is not None:
            self.call(initial_state)
        if not os.path.exists(self.args.model_dir):
            os.makedirs(self.args.model_dir)
        model_path = os.path.join(self.args.model_dir, self.args.model_name)

        if do_init and self.args.init_model_from is not None:
            init_model_path = os.path.join(
                self.args.init_model_from, self.args.model_name
            )
            if os.path.exists(init_model_path):
                print(f"initialize model weights from: {init_model_path}")
                copyfile(init_model_path, model_path)
            else:
                raise ValueError(f"could not initialize model from: {init_model_path}")

        if os.path.exists(model_path):
            if do_init:
                print("Loading model from: {}".format(model_path))
            self.load_weights(model_path)

    def save(self):
        if not os.path.exists(self.args.model_dir):
            os.makedirs(self.args.model_dir)
        model_path = os.path.join(self.args.model_dir, self.args.model_name)
        print("Save model: {}".format(model_path))
        self.save_weights(model_path, save_format="tf")

    def call_masked(self, inputs, mask) -> Tuple[tf.Tensor, tf.Tensor, tf.Tensor]:
        logits, values = self.call(inputs)
        flat_logits = tf.reshape(tf.squeeze(logits), [-1])
        probs = tf.nn.softmax(flat_logits).numpy()
        return logits, values, probs
