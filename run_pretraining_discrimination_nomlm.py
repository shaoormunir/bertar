# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Run masked LM/next sentence masked_lm pre-training for BERT."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import modeling
import optimization
import tensorflow as tf
import pandas as pd

flags = tf.flags

FLAGS = flags.FLAGS

# Required parameters
flags.DEFINE_string(
    "bert_config_file", "bert_config.json",
    "The config json file corresponding to the pre-trained BERT model. "
    "This specifies the model architecture.")

flags.DEFINE_string(
    "input_file", "gs://bert-checkpoints/input-data/train_data_new_balanced.tf_record-task-nsp",
    "Input TF example files (can be a glob or comma separated).")

flags.DEFINE_string(
    "output_dir", "gs://bert-checkpoints-test/bertar-nomlm/base-model-run-1",
    "The output directory where the model checkpoints will be written.")

# Other parameters
flags.DEFINE_string(
    "init_checkpoint", None,
    "Initial checkpoint (usually from4/zwGj5Y8jiq9vCnwI-msPcasEWSI2-gMBBEH9iu6iFiFsQkq7RPv1WO8 a pre-trained BERT model).")

flags.DEFINE_integer(
    "max_seq_length", 64,
    "The maximum total input sequence length after WordPiece tokenization. "
    "Sequences longer than this will be truncated, and sequences shorter "
    "than this will be padded. Must match data generation.")

flags.DEFINE_integer(
    "max_predictions_per_seq", 20,
    "Maximum number of masked LM predictions per sequence. "
    "Must match data generation.")

flags.DEFINE_bool("do_train", True, "Whether to run training.")

flags.DEFINE_bool("do_eval", False, "Whether to run eval on the dev set.")

flags.DEFINE_integer("train_batch_size", 32, "Total batch size for training.")

flags.DEFINE_integer("eval_batch_size", 8, "Total batch size for eval.")

flags.DEFINE_float("learning_rate", 5e-5,
                   "The initial learning rate for Adam.")

flags.DEFINE_integer("num_train_steps", 100000, "Number of training steps.")

flags.DEFINE_integer("num_warmup_steps", 10000, "Number of warmup steps.")

flags.DEFINE_integer("save_checkpoints_steps", 100000,
                     "How often to save the model checkpoint.")

flags.DEFINE_integer("save_summary_steps", 1000,
                     "How often to save the model summaries.")

flags.DEFINE_integer("iterations_per_loop", 1000,
                     "How many steps to make in each estimator call.")

flags.DEFINE_integer("max_eval_steps", 1000, "Maximum number of eval steps.")

flags.DEFINE_bool("use_tpu", True, "Whether to use TPU or GPU/CPU.")

tf.flags.DEFINE_string(
    "tpu_name", 'grpc://' + os.environ['COLAB_TPU_ADDR'],
    "The Cloud TPU to use for training. This should be either the name "
    "used when creating the Cloud TPU, or a grpc://ip.address.of.tpu:8470 "
    "url.")

tf.flags.DEFINE_string(
    "tpu_zone", None,
    "[Optional] GCE zone where the Cloud TPU is located in. If not "
    "specified, we will attempt to automatically detect the GCE project from "
    "metadata.")

tf.flags.DEFINE_string(
    "gcp_project", None,
    "[Optional] Project name for the Cloud TPU-enabled project. If not "
    "specified, we will attempt to automatically detect the GCE project from "
    "metadata.")

tf.flags.DEFINE_string("master", None, "[Optional] TensorFlow master URL.")

flags.DEFINE_integer(
    "num_tpu_cores", 8,
    "Only used if `use_tpu` is True. Total number of TPU cores to use.")

  
# class SaveMetricsHook(tf.train.SessionRunHook):
#   """Prints the given tensors every N local steps, every N seconds, or at end.
#   The tensors will be printed to the log, with `INFO` severity. If you are not
#   seeing the logs, you might want to add the following line after your imports:
#   ```python
#     tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)
#   ```
#   Note that if `at_end` is True, `tensors` should not include any tensor
#   whose evaluation produces a side effect such as consuming additional inputs.
#   """
#   def before_run(self, run_context):  # pylint: disable=unused-argument
#      graph = run_context.session.graph
#      self.total_loss = graph.get_tensor_by_name("total_loss:0")
#      self.synthetic_prediction_loss = graph.get_tensor_by_name("synthetic_prediction_loss:0")
#      self.next_sentence_loss = graph.get_tensor_by_name("next_sentence_loss:0")
#      self.masked_lm_loss = graph.get_tensor_by_name("masked_lm_loss:0")
#      self.encoder_layers = graph.get_tensor_by_name("encoder_layers:0")
#      self.pooled_output = graph.get_tensor_by_name("pooled_output:0")
#      self.finalized = graph.finalized

#   def after_run(self, run_context, run_values):
#     #  total_loss = run_values.results[0]
#     #  synthetic_prediction_loss = run_values.results[0]
#     #  next_sentence_loss = run_values.results[0]
#     #  masked_lm_loss = run_values.results[0]
#     #  encoder_layers = run_values.results[0]
#     #  pooled_output = run_values.results[0]

#     # df = pd.DataFrame(columns = ("total_loss", "synthetic_prediction_loss","next_sentence_loss","masked_lm_loss"))
#     # df = df.append({"total_loss":self.total_loss.eval(session=run_context.session), "synthetic_prediction_loss":self.synthetic_prediction_loss.eval(session=run_context.session),"next_sentence_loss":self.next_sentence_loss.eval(session=run_context.session),"masked_lm_loss":self.masked_lm_loss.eval(session=run_context.session)}, ignore_index=True)
#     # df.to_csv("loss.csv", mode='a'https://www.blue-ex.com/tracking?trackno=5011841517, header=False)
#     # df.to_csv(FLAGS.output_dir+"/loss.csv", mode='a', header=False)

#     if not self.finalized:
#       tf.contrib.summary.scalar("total_loss",self.total_loss)
#       tf.contrib.summary.scalar("synthetic_prediction_loss", self.synthetic_prediction_loss)
#       tf.contrib.summary.scalar("next_sentence_loss",self.next_sentence_loss)
#       tf.contrib.summary.scalar("masked_lm_loss", self.masked_lm_loss)
#       tf.contrib.summary.histogram(
#           "encoder_layers", self.encoder_layers)
#       tf.contrib.summary.histogram("pooled_output", self.pooled_output)
#       tf.summary.merge_all()


def model_fn_builder(bert_config, init_checkpoint, learning_rate,
                     num_train_steps, num_warmup_steps, use_tpu,
                     use_one_hot_embeddings):
  """Returns `model_fn` closure for TPUEstimator."""

  def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
    """The `model_fn` for TPUEstimator."""

    tf.logging.info("*** Features ***")
    for name in sorted(features.keys()):
      tf.logging.info("  name = %s, shape = %s" % (name, features[name].shape))

    input_ids = features["input_ids"]
    input_mask = features["input_mask"]
    segment_ids = features["segment_ids"]
    next_sentence_labels = features["next_sentence_labels"]
    synthetic_labels = features["synthetic_text_labels"]

    is_training = (mode == tf.estimator.ModeKeys.TRAIN)

    model = modeling.BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=input_mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=use_one_hot_embeddings)

    # This is where the model is calculating the total loss occurred over the two training strategies, and we can add the third strategy here

    (next_sentence_loss, next_sentence_example_loss,
     next_sentence_log_probs) = get_next_sentence_output(
         bert_config, model.get_pooled_output(), next_sentence_labels)

    (synthetic_loss, synthetic_example_loss,
     synthetic_log_probs) = get_synthetic_text_output(
         bert_config, model.get_pooled_output(), synthetic_labels)

    # The third loss will be added here

    total_loss = next_sentence_loss + synthetic_loss

    # tf.identity(total_loss, name='total_loss')
    # tf.identity(synthetic_loss, name='synthetic_prediction_loss')
    # tf.identity(next_sentence_loss, name='next_sentence_loss')
    # tf.identity(masked_lm_loss, name='masked_lm_loss')
    # tf.identity(model.get_all_encoder_layers(), name='encoder_layers')
    # tf.identity(model.get_pooled_output(), name='pooled_output')

    # tf.summary.scalar("total_loss",tf.convert_to_tensor(total_loss, dtype=tf.float32))
    # tf.summary.scalar("synthetic_prediction_loss", tf.convert_to_tensor(synthetic_loss, dtype=tf.float32))
    # tf.summary.scalar("next_sentence_loss", tf.convert_to_tensor(next_sentence_loss, dtype=tf.float32) )
    # tf.summary.scalar("masked_lm_loss", tf.convert_to_tensor(masked_lm_loss, dtype=tf.float32))
    # tf.summary.histogram(
    #     "encoder_layers", model.get_all_encoder_layers())
    # tf.summary.histogram("pooled_output", model.get_pooled_output())


    # train_summary_hook = tf.train.SummarySaverHook(
    #                             save_steps=1,
    #                             output_dir= FLAGS.output_dir + "/test_summaries",
    #                             scaffold=tf.train.Scaffold(summary_op=tf.summary.merge_all()))

    tvars = tf.trainable_variables()

    initialized_variable_names = {}
    scaffold_fn = None
    if init_checkpoint:
      (assignment_map, initialized_variable_names
      ) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)
      if use_tpu:
        def tpu_scaffold():
          tf.summary.merge_all()
          tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
          return tf.train.Scaffold()

        scaffold_fn = tpu_scaffold
      else:
        def scaffold_temp():
          tf.summary.merge_all()
        scaffold_fn = scaffold_temp
        tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

    tf.logging.info("**** Trainable Variables ****")
    for var in tvars:
      init_string = ""
      if var.name in initialized_variable_names:
        init_string = ", *INIT_FROM_CKPT*"
      tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                      init_string)

    output_spec = None
    if mode == tf.estimator.ModeKeys.TRAIN:
      train_op = optimization.create_optimizer(
          total_loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu)

      output_spec = tf.contrib.tpu.TPUEstimatorSpec(
          mode=mode,
          loss=total_loss,
          train_op=train_op,
          scaffold_fn=scaffold_fn)
    elif mode == tf.estimator.ModeKeys.EVAL:

      def metric_fn(next_sentence_example_loss,
                    next_sentence_log_probs, next_sentence_labels, synthetic_example_loss, synthetic_log_probs, synthetic_labels):
        """Computes the loss and accuracy of the model."""

        next_sentence_log_probs = tf.reshape(
            next_sentence_log_probs, [-1, next_sentence_log_probs.shape[-1]])
        next_sentence_predictions = tf.argmax(
            next_sentence_log_probs, axis=-1, output_type=tf.int32)
        next_sentence_labels = tf.reshape(next_sentence_labels, [-1])
        next_sentence_accuracy = tf.metrics.accuracy(
            labels=next_sentence_labels, predictions=next_sentence_predictions)
        next_sentence_mean_loss = tf.metrics.mean(
            values=next_sentence_example_loss)

        synthetic_log_probs = tf.reshape(
            synthetic_log_probs, [-1, synthetic_log_probs.shape[-1]])
        synthetic_predictions = tf.argmax(
            synthetic_log_probs, axis=-1, output_type=tf.int32)
        synthetic_labels = tf.reshape(synthetic_labels, [-1])
        synthetic_accuracy = tf.metrics.accuracy(
            labels=synthetic_labels, predictions=synthetic_predictions)
        synthetic_mean_loss = tf.metrics.mean(
            values=synthetic_example_loss)

        # tf.contrib.summary.scalar("masked_lm_accuracy",masked_lm_accuracy)
        # tf.contrib.summary.scalar("masked_lm_loss", masked_lm_mean_loss)
        # tf.contrib.summary.scalar("next_sentence_accuracy",next_sentence_accuracy)
        # tf.contrib.summary.scalar("next_sentence_loss", next_sentence_mean_loss)
        # tf.contrib.summary.scalar("synthetic_accuracy", synthetic_accuracy)
        # tf.contrib.summary.scalar("synthetic_mean_loss", synthetic_mean_loss)
        # tf.contrib.summary.histogram(
        #     "synthetic_accuracy", model.get_all_encoder_layers())
        # tf.contrib.summary.histogram("pooled_output", model.get_pooled_output())

        return {
            "next_sentence_accuracy": next_sentence_accuracy,
            "next_sentence_loss": next_sentence_mean_loss,
            "synthetic_accuracy": synthetic_accuracy,
            "synthetic_mean_loss": synthetic_mean_loss
        }

      eval_metrics = (metric_fn, [next_sentence_example_loss,
          next_sentence_log_probs, next_sentence_labels, synthetic_example_loss, synthetic_log_probs, synthetic_labels
      ])
      output_spec = tf.contrib.tpu.TPUEstimatorSpec(
          mode=mode,
          loss=total_loss,
          eval_metrics=eval_metrics,
          scaffold_fn=scaffold_fn)
    else:
      raise ValueError("Only TRAIN and EVAL modes are supported: %s" % (mode))

    return output_spec

  return model_fn

def get_next_sentence_output(bert_config, input_tensor, labels):
  """Get loss and log probs for the next sentence prediction."""

  # Simple binary classification. Note that 0 is "next sentence" and 1 is
  # "random sentence". This weight matrix is not used after pre-training.
  with tf.variable_scope("cls/seq_relationship"):
    output_weights = tf.get_variable(
        "output_weights",
        shape=[2, bert_config.hidden_size],
        initializer=modeling.create_initializer(bert_config.initializer_range))
    output_bias = tf.get_variable(
        "output_bias", shape=[2], initializer=tf.zeros_initializer())

    logits = tf.matmul(input_tensor, output_weights, transpose_b=True)
    logits = tf.nn.bias_add(logits, output_bias)
    log_probs = tf.nn.log_softmax(logits, axis=-1)
    labels = tf.reshape(labels, [-1])
    one_hot_labels = tf.one_hot(labels, depth=2, dtype=tf.float32)
    per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
    loss = tf.reduce_mean(per_example_loss)
    return (loss, per_example_loss, log_probs)


def get_synthetic_text_output(bert_config, input_tensor, labels):
  """Get loss and log probs for the next sentence prediction."""

  # Simple binary classification. Note that 0 is "organic" and 1 is
  # "synthetic". This weight matrix is not used after pre-training.
  with tf.variable_scope("cls/synthetic_discrimination"):
    output_weights = tf.get_variable(
        "output_weights",
        shape=[2, bert_config.hidden_size],
        initializer=modeling.create_initializer(bert_config.initializer_range))
    output_bias = tf.get_variable(
        "output_bias", shape=[2], initializer=tf.zeros_initializer())

    logits = tf.matmul(input_tensor, output_weights, transpose_b=True)
    logits = tf.nn.bias_add(logits, output_bias)
    log_probs = tf.nn.log_softmax(logits, axis=-1)
    labels = tf.reshape(labels, [-1])
    one_hot_labels = tf.one_hot(labels, depth=2, dtype=tf.float32)
    per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
    loss = tf.reduce_mean(per_example_loss)
    return (loss, per_example_loss, log_probs)


def gather_indexes(sequence_tensor, positions):
  """Gathers the vectors at the specific positions over a minibatch."""
  sequence_shape = modeling.get_shape_list(sequence_tensor, expected_rank=3)
  batch_size = sequence_shape[0]
  seq_length = sequence_shape[1]
  width = sequence_shape[2]

  flat_offsets = tf.reshape(
      tf.range(0, batch_size, dtype=tf.int32) * seq_length, [-1, 1])
  flat_positions = tf.reshape(positions + flat_offsets, [-1])
  flat_sequence_tensor = tf.reshape(sequence_tensor,
                                    [batch_size * seq_length, width])
  output_tensor = tf.gather(flat_sequence_tensor, flat_positions)
  return output_tensor


def input_fn_builder(input_files,
                     max_seq_length,
                     max_predictions_per_seq,
                     is_training,
                     num_cpu_threads=4):
  """Creates an `input_fn` closure to be passed to TPUEstimator."""

  def input_fn(params):
    """The actual input function."""
    batch_size = params["batch_size"]

    name_to_features = {
        "input_ids":
            tf.FixedLenFeature([max_seq_length], tf.int64),
        "input_mask":
            tf.FixedLenFeature([max_seq_length], tf.int64),
        "segment_ids":
            tf.FixedLenFeature([max_seq_length], tf.int64),
        "masked_lm_positions":
            tf.FixedLenFeature([max_predictions_per_seq], tf.int64),
        "masked_lm_ids":
            tf.FixedLenFeature([max_predictions_per_seq], tf.int64),
        "masked_lm_weights":
            tf.FixedLenFeature([max_predictions_per_seq], tf.float32),
        "next_sentence_labels":
            tf.FixedLenFeature([1], tf.int64),
        "synthetic_text_labels":
            tf.FixedLenFeature([1], tf.int64),
    }

    # For training, we want a lot of parallel reading and shuffling.
    # For eval, we want no shuffling and parallel reading doesn't matter.
    if is_training:
      d = tf.data.Dataset.from_tensor_slices(tf.constant(input_files))
      d = d.repeat()
      d = d.shuffle(buffer_size=len(input_files))

      # `cycle_length` is the number of parallel files that get read.
      cycle_length = min(num_cpu_threads, len(input_files))

      # `sloppy` mode means that the interleaving is not exact. This adds
      # even more randomness to the training pipeline.
      d = d.apply(
          tf.contrib.data.parallel_interleave(
              tf.data.TFRecordDataset,
              sloppy=is_training,
              cycle_length=cycle_length))
      d = d.shuffle(buffer_size=100)
    else:
      d = tf.data.TFRecordDataset(input_files)
      # Since we evaluate for a fixed number of steps we don't want to encounter
      # out-of-range exceptions.
      d = d.repeat()

    # We must `drop_remainder` on training because the TPU requires fixed
    # size dimensions. For eval, we assume we are evaluating on the CPU or GPU
    # and we *don't* want to drop the remainder, otherwise we wont cover
    # every sample.
    d = d.apply(
        tf.contrib.data.map_and_batch(
            lambda record: _decode_record(record, name_to_features),
            batch_size=batch_size,
            num_parallel_batches=num_cpu_threads,
            drop_remainder=True))
    return d

  return input_fn


def _decode_record(record, name_to_features):
  """Decodes a record to a TensorFlow example."""
  example = tf.parse_single_example(record, name_to_features)

  # tf.Example only supports tf.int64, but the TPU only supports tf.int32.
  # So cast all int64 to int32.
  for name in list(example.keys()):
    t = example[name]
    if t.dtype == tf.int64:
      t = tf.to_int32(t)
    example[name] = t

  return example


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)

  if not FLAGS.do_train and not FLAGS.do_eval:
    raise ValueError("At least one of `do_train` or `do_eval` must be True.")

  bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)

  tf.gfile.MakeDirs(FLAGS.output_dir)

  input_files = []
  for input_pattern in FLAGS.input_file.split(","):
    input_files.extend(tf.gfile.Glob(input_pattern))

  tf.logging.info("*** Input Files ***")
  for input_file in input_files:
    tf.logging.info("  %s" % input_file)

  tpu_cluster_resolver = None
  if FLAGS.use_tpu and FLAGS.tpu_name:
    tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
        FLAGS.tpu_name, zone=FLAGS.tpu_zone, project=FLAGS.gcp_project)

  is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
  run_config = tf.contrib.tpu.RunConfig(
      cluster=tpu_cluster_resolver,
      master=FLAGS.master,
      model_dir=FLAGS.output_dir,
      save_checkpoints_steps=FLAGS.save_checkpoints_steps,
      save_summary_steps=FLAGS.save_summary_steps,
      tpu_config=tf.contrib.tpu.TPUConfig(
          iterations_per_loop=FLAGS.iterations_per_loop,
          num_shards=FLAGS.num_tpu_cores,
          per_host_input_for_training=is_per_host))

  model_fn = model_fn_builder(
      bert_config=bert_config,
      init_checkpoint=FLAGS.init_checkpoint,
      learning_rate=FLAGS.learning_rate,
      num_train_steps=FLAGS.num_train_steps,
      num_warmup_steps=FLAGS.num_warmup_steps,
      use_tpu=FLAGS.use_tpu,
      use_one_hot_embeddings=FLAGS.use_tpu)

  # If TPU is not available, this will fall back to normal Estimator on CPU
  # or GPU.
  estimator = tf.contrib.tpu.TPUEstimator(
      use_tpu=FLAGS.use_tpu,
      model_fn=model_fn,
      config=run_config,
      train_batch_size=FLAGS.train_batch_size,
      eval_batch_size=FLAGS.eval_batch_size)

  if FLAGS.do_train:
    tf.logging.info("***** Running training *****")
    tf.logging.info("  Batch size = %d", FLAGS.train_batch_size)
    train_input_fn = input_fn_builder(
        input_files=input_files,
        max_seq_length=FLAGS.max_seq_length,
        max_predictions_per_seq=FLAGS.max_predictions_per_seq,
        is_training=True)
    estimator.train(input_fn=train_input_fn, max_steps=FLAGS.num_train_steps)

  if FLAGS.do_eval:
    tf.logging.info("***** Running evaluation *****")
    tf.logging.info("  Batch size = %d", FLAGS.eval_batch_size)

    eval_input_fn = input_fn_builder(
        input_files=input_files,
        max_seq_length=FLAGS.max_seq_length,
        max_predictions_per_seq=FLAGS.max_predictions_per_seq,
        is_training=False)

    result = estimator.evaluate(
        input_fn=eval_input_fn, steps=FLAGS.max_eval_steps)

    output_eval_file = os.path.join(FLAGS.output_dir, "eval_results.txt")
    with tf.gfile.GFile(output_eval_file, "w") as writer:
      tf.logging.info("***** Eval results *****")
      for key in sorted(result.keys()):
        tf.logging.info("  %s = %s", key, str(result[key]))
        writer.write("%s = %s\n" % (key, str(result[key])))


if __name__ == "__main__":
  flags.mark_flag_as_required("input_file")
  flags.mark_flag_as_required("bert_config_file")
  flags.mark_flag_as_required("output_dir")
  tf.app.run()