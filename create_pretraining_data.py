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
"""Create masked LM/next sentence masked_lm TF examples for BERT."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import random
import tokenization
import tensorflow as tf

flags = tf.flags

FLAGS = flags.FLAGS

flags.DEFINE_string("input_file_synthetic", "/content/drive/My Drive/bert-vocab-and-data-new/machine.train.0.txt",
                    "Input raw text file (or comma-separated list of files).")

flags.DEFINE_string("input_file_organic", "/content/drive/My Drive/bert-vocab-and-data-new/human.train.0.txt",
                    "Input raw text file (or comma-separated list of files).")

flags.DEFINE_string(
    "output_file", "/content/drive/My Drive/iowa-project-2/train_data_new_balanced.tf_record",
    "Output TF example file (or comma-separated list of files).")

flags.DEFINE_string("vocab_file", "vocab.txt",
                    "The vocabulary file that the BERT model was trained on.")

flags.DEFINE_bool(
    "do_lower_case", True,
    "Whether to lower case the input text. Should be True for uncased "
    "models and False for cased models.")

flags.DEFINE_bool(
    "do_whole_word_mask", False,
    "Whether to use whole word masking rather than per-WordPiece masking.")

flags.DEFINE_integer("max_seq_length", 64, "Maximum sequence length.")

flags.DEFINE_integer("max_predictions_per_seq", 20,
                     "Maximum number of masked LM predictions per sequence.")

flags.DEFINE_integer("random_seed", 12345, "Random seed for data generation.")

flags.DEFINE_integer(
    "dupe_factor", 10,
    "Number of times to duplicate the input data (with different masks).")

flags.DEFINE_float("masked_lm_prob", 0.15, "Masked LM probability.")

flags.DEFINE_float(
    "short_seq_prob", 0.2,
    "Probability of creating sequences which are shorter than the "
    "maximum length.")


class TrainingInstance(object):
  """A single training instance (sentence pair)."""

  def __init__(self, tokens, tokens_a, tokens_b, segment_ids, masked_lm_positions, masked_lm_labels, masked_lm_positions_a, masked_lm_labels_a, masked_lm_positions_b, masked_lm_labels_b,
               is_random_next, is_synthetic):
    self.tokens = tokens
    self.tokens_a = tokens_a
    self.tokens_b = tokens_b
    self.segment_ids = segment_ids
    self.is_random_next = is_random_next
    self.masked_lm_positions = masked_lm_positions
    self.masked_lm_labels = masked_lm_labels
    self.masked_lm_positions_a = masked_lm_positions_a
    self.masked_lm_labels_a = masked_lm_labels_a
    self.masked_lm_positions_b = masked_lm_positions_b
    self.masked_lm_labels_b = masked_lm_labels_b
    self.is_synthetic = is_synthetic

  def __str__(self):
    s = ""
    s += "tokens: %s\n" % (" ".join(
        [tokenization.printable_text(x) for x in self.tokens]))
    s += "segment_ids: %s\n" % (" ".join([str(x) for x in self.segment_ids]))
    s += "is_random_next: %s\n" % self.is_random_next
    s += "is_synthetic: %s\n" % self.is_synthetic
    s += "masked_lm_positions: %s\n" % (" ".join(
        [str(x) for x in self.masked_lm_positions]))
    s += "masked_lm_labels: %s\n" % (" ".join(
        [tokenization.printable_text(x) for x in self.masked_lm_labels]))
    s += "\n"
    return s

  def __repr__(self):
    return self.__str__()


def write_instance_to_example_files(instances, tokenizer, max_seq_length,
                                    max_predictions_per_seq, output_files):
  """Create TF example files from `TrainingInstance`s."""
  writers = []
  writers.append(tf.python_io.TFRecordWriter(FLAGS.output_file+"-task-nsp"))
  writers.append(tf.python_io.TFRecordWriter(FLAGS.output_file+"-task-nonsp"))

  total_written = 0
  for (inst_index, instance) in enumerate(instances):
    input_ids = tokenizer.convert_tokens_to_ids(instance.tokens)
    input_mask = [1] * len(input_ids)
    segment_ids = list(instance.segment_ids)
    assert len(input_ids) <= max_seq_length

    while len(input_ids) < max_seq_length:
      input_ids.append(0)
      input_mask.append(0)
      segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    masked_lm_positions = list(instance.masked_lm_positions)
    masked_lm_ids = tokenizer.convert_tokens_to_ids(instance.masked_lm_labels)
    masked_lm_weights = [1.0] * len(masked_lm_ids)

    while len(masked_lm_positions) < max_predictions_per_seq:
      masked_lm_positions.append(0)
      masked_lm_ids.append(0)
      masked_lm_weights.append(0.0)

    next_sentence_label = 1 if instance.is_random_next else 0
    synthetic_label = 1 if instance.is_synthetic else 0

    features = collections.OrderedDict()
    features["input_ids"] = create_int_feature(input_ids)
    features["input_mask"] = create_int_feature(input_mask)
    features["segment_ids"] = create_int_feature(segment_ids)
    features["masked_lm_positions"] = create_int_feature(masked_lm_positions)
    features["masked_lm_ids"] = create_int_feature(masked_lm_ids)
    features["masked_lm_weights"] = create_float_feature(masked_lm_weights)
    features["next_sentence_labels"] = create_int_feature([next_sentence_label])
    features["synthetic_text_labels"] = create_int_feature([synthetic_label])

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))

    writers[0].write(tf_example.SerializeToString())

    if inst_index < 20:
      tf.logging.info("*** Example ***")
      tf.logging.info("tokens: %s" % " ".join(
          [tokenization.printable_text(x) for x in instance.tokens]))

      for feature_name in features.keys():
        feature = features[feature_name]
        values = []
        if feature.int64_list.value:
          values = feature.int64_list.value
        elif feature.float_list.value:
          values = feature.float_list.value
        tf.logging.info(
            "%s: %s" % (feature_name, " ".join([str(x) for x in values])))

    # Writing for token a from here
    input_ids = tokenizer.convert_tokens_to_ids(instance.tokens_a)
    input_mask = [1] * len(input_ids)
    segment_ids = [0] * len(input_ids)
    assert len(input_ids) <= max_seq_length

    while len(input_ids) < max_seq_length:
      input_ids.append(0)
      input_mask.append(0)
      segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    masked_lm_positions = list(instance.masked_lm_positions_a)
    masked_lm_ids = tokenizer.convert_tokens_to_ids(instance.masked_lm_labels_a)
    masked_lm_weights = [1.0] * len(masked_lm_ids)

    while len(masked_lm_positions) < max_predictions_per_seq:
      masked_lm_positions.append(0)
      masked_lm_ids.append(0)
      masked_lm_weights.append(0.0)

    synthetic_label = 1 if instance.is_synthetic else 0
    next_sentence_label = 0

    features = collections.OrderedDict()
    features["input_ids"] = create_int_feature(input_ids)
    features["input_mask"] = create_int_feature(input_mask)
    features["segment_ids"] = create_int_feature(segment_ids)
    features["masked_lm_positions"] = create_int_feature(masked_lm_positions)
    features["masked_lm_ids"] = create_int_feature(masked_lm_ids)
    features["masked_lm_weights"] = create_float_feature(masked_lm_weights)
    features["next_sentence_labels"] = create_int_feature([next_sentence_label])
    features["synthetic_text_labels"] = create_int_feature([synthetic_label])

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))

    writers[1].write(tf_example.SerializeToString())

    if inst_index < 20:
      tf.logging.info("*** Example ***")
      tf.logging.info("tokens: %s" % " ".join(
          [tokenization.printable_text(x) for x in instance.tokens]))

      for feature_name in features.keys():
        feature = features[feature_name]
        values = []
        if feature.int64_list.value:
          values = feature.int64_list.value
        elif feature.float_list.value:
          values = feature.float_list.value
        tf.logging.info(
            "%s: %s" % (feature_name, " ".join([str(x) for x in values])))
    
    #writing for token b from here
    input_ids = tokenizer.convert_tokens_to_ids(instance.tokens_b)
    input_mask = [1] * len(input_ids)
    segment_ids = [0] * len(input_ids)
    assert len(input_ids) <= max_seq_length

    while len(input_ids) < max_seq_length:
      input_ids.append(0)
      input_mask.append(0)
      segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    masked_lm_positions = list(instance.masked_lm_positions_b)
    masked_lm_ids = tokenizer.convert_tokens_to_ids(instance.masked_lm_labels_b)
    masked_lm_weights = [1.0] * len(masked_lm_ids)

    while len(masked_lm_positions) < max_predictions_per_seq:
      masked_lm_positions.append(0)
      masked_lm_ids.append(0)
      masked_lm_weights.append(0.0)

    synthetic_label = 1 if instance.is_synthetic else 0
    next_sentence_label = 0

    features = collections.OrderedDict()
    features["input_ids"] = create_int_feature(input_ids)
    features["input_mask"] = create_int_feature(input_mask)
    features["segment_ids"] = create_int_feature(segment_ids)
    features["masked_lm_positions"] = create_int_feature(masked_lm_positions)
    features["masked_lm_ids"] = create_int_feature(masked_lm_ids)
    features["masked_lm_weights"] = create_float_feature(masked_lm_weights)
    features["next_sentence_labels"] = create_int_feature([next_sentence_label])
    features["synthetic_text_labels"] = create_int_feature([synthetic_label])

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))

    writers[1].write(tf_example.SerializeToString())
     
    if inst_index < 20:
      tf.logging.info("*** Example ***")
      tf.logging.info("tokens: %s" % " ".join(
          [tokenization.printable_text(x) for x in instance.tokens]))

      for feature_name in features.keys():
        feature = features[feature_name]
        values = []
        if feature.int64_list.value:
          values = feature.int64_list.value
        elif feature.float_list.value:
          values = feature.float_list.value
        tf.logging.info(
            "%s: %s" % (feature_name, " ".join([str(x) for x in values])))

    total_written += 1

  for writer in writers:
    writer.close()

  tf.logging.info("Wrote %d total instances", total_written)

def create_int_feature(values):
  feature = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
  return feature


def create_float_feature(values):
  feature = tf.train.Feature(float_list=tf.train.FloatList(value=list(values)))
  return feature


def create_training_instances(input_files, tokenizer, max_seq_length, is_synthetic,
                              dupe_factor, short_seq_prob, masked_lm_prob,
                              max_predictions_per_seq, rng):
  """Create `TrainingInstance`s from raw text."""
  all_documents = [[]]
  labels = [is_synthetic]

  # Input file format:
  # (1) One sentence per line. These should ideally be actual sentences, not
  # entire paragraphs or arbitrary spans of text. (Because we use the
  # sentence boundaries for the "next sentence prediction" task).
  # (2) Blank lines between documents. Document boundaries are needed so
  # that the "next sentence prediction" task doesn't span between documents.

  #BERTAR modifications: maintaining labels for now too with the documents, to be used later on with training

  for input_file in input_files:
    with tf.gfile.GFile(input_file, "r") as reader:
      while True:
        line = tokenization.convert_to_unicode(reader.readline())
        if not line:
          break
        line = line.strip()

        # Empty lines are used as document delimiters
        if not line:
          all_documents.append([])
          labels.append(is_synthetic)
        tokens = tokenizer.tokenize(line)
        if tokens:
          all_documents[-1].append(tokens)
  
  for i, doc in enumerate(all_documents):
    if not doc:
      all_documents.pop(i)
      labels.pop(i)
  # # Remove empty documents
  # all_documents = [x for x in all_documents if x]
  temp_list = list(zip(all_documents, labels))
  rng.shuffle(temp_list)
  all_documents, labels = zip(*temp_list)
  all_documents = list(all_documents)
  labels = list(labels)
  vocab_words = list(tokenizer.vocab.keys())

  instances = []
  for _ in range(dupe_factor):
    for document_index in range(len(all_documents)):
      instances.extend(
          create_instances_from_document(
              all_documents, labels, document_index, max_seq_length, short_seq_prob,
              masked_lm_prob, max_predictions_per_seq, vocab_words, rng))
  return instances


def create_instances_from_document(
    all_documents, labels, document_index, max_seq_length, short_seq_prob,
    masked_lm_prob, max_predictions_per_seq, vocab_words, rng):
  """Creates `TrainingInstance`s for a single document."""
  document = all_documents[document_index]
  label = labels[document_index]

  # Account for [CLS], [SEP], [SEP]
  max_num_tokens = max_seq_length - 3

  # We *usually* want to fill up the entire sequence since we are padding
  # to `max_seq_length` anyways, so short sequences are generally wasted
  # computation. However, we *sometimes*
  # (i.e., short_seq_prob == 0.1 == 10% of the time) want to use shorter
  # sequences to minimize the mismatch between pre-training and fine-tuning.
  # The `target_seq_length` is just a rough target however, whereas
  # `max_seq_length` is a hard limit.
  target_seq_length = max_num_tokens
  if rng.random() < short_seq_prob:
    target_seq_length = rng.randint(2, max_num_tokens)

  # We DON'T just concatenate all of the tokens from a document into a long
  # sequence and choose an arbitrary split point because this would make the
  # next sentence prediction task too easy. Instead, we split the input into
  # segments "A" and "B" based on the actual "sentences" provided by the user
  # input.
  instances = []
  current_chunk = []
  current_length = 0
  i = 0
  while i < len(document):
    segment = document[i]
    current_chunk.append(segment)
    current_length += len(segment)
    if i == len(document) - 1 or current_length >= target_seq_length:
      if current_chunk:
        # `a_end` is how many segments from `current_chunk` go into the `A`
        # (first) sentence.
        a_end = 1
        if len(current_chunk) >= 2:
          a_end = rng.randint(1, len(current_chunk) - 1)

        tokens_a = []
        for j in range(a_end):
          tokens_a.extend(current_chunk[j])
        
        test_tokens = []
        for j in range(a_end, len(current_chunk)):
            test_tokens.extend(current_chunk[j])
        
        no_next_sentence = len(test_tokens) == 0

        tokens_b = []
        # Random next
        is_random_next = False
        if len(current_chunk) == 1 or rng.random() < 0.5 or no_next_sentence:
          is_random_next = True
          target_b_length = target_seq_length - len(tokens_a)

          # This should rarely go for more than one iteration for large
          # corpora. However, just to be careful, we try to make sure that
          # the random document is not the same as the document
          # we're processing.
          for _ in range(100):
            random_document_index = rng.randint(0, len(all_documents) - 1)
            if random_document_index != document_index and len(all_documents[random_document_index]) > 1:
              break

          random_document = all_documents[random_document_index]
          random_start = rng.randint(0, len(random_document) - 1)
          for j in range(random_start, len(random_document)):
            tokens_b.extend(random_document[j])
            if len(tokens_b) >= target_b_length:
              break
          # We didn't actually use these segments so we "put them back" so
          # they don't go to waste.
          num_unused_segments = len(current_chunk) - a_end
          i -= num_unused_segments
        # Actual next
        else:
          is_random_next = False
          for j in range(a_end, len(current_chunk)):
            tokens_b.extend(current_chunk[j])
        
        tokens_first = tokens_a.copy()
        tokens_second = tokens_b.copy()
        truncate_seq_pair(tokens_a, tokens_b, max_num_tokens, rng)
        truncate_seq_pair(tokens_first, [], max_num_tokens+1, rng)
        truncate_seq_pair(tokens_second, [], max_num_tokens+1, rng)

        assert len(tokens_a) >= 1
        assert len(tokens_b) >= 1
        assert len(tokens_first) >= 1
        assert len(tokens_second) >= 1

        tokens = []
        tokens_senta = []
        tokens_sentb = []
        segment_ids = []
        tokens.append("[CLS]")
        tokens_senta.append("[CLS]")
        segment_ids.append(0)
        for token in tokens_a:
          tokens.append(token)
          segment_ids.append(0)
        
        for token in tokens_first:
          tokens_senta.append(token)

        tokens.append("[SEP]")
        tokens_senta.append("[SEP]")

        segment_ids.append(0)
        tokens_sentb.append("[CLS]")
        
        for token in tokens_b:
          tokens.append(token)
          segment_ids.append(1)

        for token in tokens_second:
          tokens_sentb.append(token)
        
        tokens.append("[SEP]")
        tokens_sentb.append("[SEP]")
        
        segment_ids.append(1)

        (tokens, masked_lm_positions,
         masked_lm_labels) = create_masked_lm_predictions(
             tokens, masked_lm_prob, max_predictions_per_seq, vocab_words, rng)
        
        (tokens_senta, masked_lm_positions_a,
         masked_lm_labels_a) = create_masked_lm_predictions(
             tokens_senta, masked_lm_prob, max_predictions_per_seq, vocab_words, rng)

        (tokens_sentb, masked_lm_positions_b,
         masked_lm_labels_b) = create_masked_lm_predictions(
             tokens_sentb, masked_lm_prob, max_predictions_per_seq, vocab_words, rng)

        instance = TrainingInstance(
            tokens=tokens,
            tokens_a=tokens_senta,
            tokens_b=tokens_sentb,
            segment_ids=segment_ids,
            is_random_next=is_random_next,
            masked_lm_positions=masked_lm_positions,
            masked_lm_labels=masked_lm_labels,
            masked_lm_positions_a=masked_lm_positions_a,
            masked_lm_labels_a=masked_lm_labels_a,
            masked_lm_positions_b=masked_lm_positions_b,
            masked_lm_labels_b=masked_lm_labels_b,
            is_synthetic=label)
        instances.append(instance)
      current_chunk = []
      current_length = 0
    i += 1

  return instances


MaskedLmInstance = collections.namedtuple("MaskedLmInstance",
                                          ["index", "label"])


def create_masked_lm_predictions(tokens, masked_lm_prob,
                                 max_predictions_per_seq, vocab_words, rng):
  """Creates the predictions for the masked LM objective."""

  cand_indexes = []
  for (i, token) in enumerate(tokens):
    if token == "[CLS]" or token == "[SEP]":
      continue
    # Whole Word Masking means that if we mask all of the wordpieces
    # corresponding to an original word. When a word has been split into
    # WordPieces, the first token does not have any marker and any subsequence
    # tokens are prefixed with ##. So whenever we see the ## token, we
    # append it to the previous set of word indexes.
    #
    # Note that Whole Word Masking does *not* change the training code
    # at all -- we still predict each WordPiece independently, softmaxed
    # over the entire vocabulary.
    if (FLAGS.do_whole_word_mask and len(cand_indexes) >= 1 and
        token.startswith("##")):
      cand_indexes[-1].append(i)
    else:
      cand_indexes.append([i])

  rng.shuffle(cand_indexes)

  output_tokens = list(tokens)

  num_to_predict = min(max_predictions_per_seq,
                       max(1, int(round(len(tokens) * masked_lm_prob))))

  masked_lms = []
  covered_indexes = set()
  for index_set in cand_indexes:
    if len(masked_lms) >= num_to_predict:
      break
    # If adding a whole-word mask would exceed the maximum number of
    # predictions, then just skip this candidate.
    if len(masked_lms) + len(index_set) > num_to_predict:
      continue
    is_any_index_covered = False
    for index in index_set:
      if index in covered_indexes:
        is_any_index_covered = True
        break
    if is_any_index_covered:
      continue
    for index in index_set:
      covered_indexes.add(index)

      masked_token = None
      # 80% of the time, replace with [MASK]
      if rng.random() < 0.8:
        masked_token = "[MASK]"
      else:
        # 10% of the time, keep original
        if rng.random() < 0.5:
          masked_token = tokens[index]
        # 10% of the time, replace with random word
        else:
          masked_token = vocab_words[rng.randint(0, len(vocab_words) - 1)]

      output_tokens[index] = masked_token

      masked_lms.append(MaskedLmInstance(index=index, label=tokens[index]))
  assert len(masked_lms) <= num_to_predict
  masked_lms = sorted(masked_lms, key=lambda x: x.index)

  masked_lm_positions = []
  masked_lm_labels = []
  for p in masked_lms:
    masked_lm_positions.append(p.index)
    masked_lm_labels.append(p.label)

  return (output_tokens, masked_lm_positions, masked_lm_labels)


def truncate_seq_pair(tokens_a, tokens_b, max_num_tokens, rng):
  """Truncates a pair of sequences to a maximum sequence length."""
  while True:
    total_length = len(tokens_a) + len(tokens_b)
    if total_length <= max_num_tokens:
      break

    trunc_tokens = tokens_a if len(tokens_a) > len(tokens_b) else tokens_b
    assert len(trunc_tokens) >= 1

    # We want to sometimes truncate from the front and sometimes from the
    # back to add more randomness and avoid biases.
    if rng.random() < 0.5:
      del trunc_tokens[0]
    else:
      trunc_tokens.pop()


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)

  tokenizer = tokenization.FullTokenizer(
      vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)

  input_files_organic = []
  input_files_synthetic = []
  for input_pattern in FLAGS.input_file_organic.split(","):
    input_files_organic.extend(tf.gfile.Glob(input_pattern))
  
  for input_pattern in FLAGS.input_file_synthetic.split(","):
    input_files_synthetic.extend(tf.gfile.Glob(input_pattern))

  shard_count = 0
  instances = []
  tf.logging.info("*** Reading from input files ***")
  for input_file in input_files_organic:
    tf.logging.info("  %s", input_file)
    rng = random.Random(FLAGS.random_seed)
    instances.extend(create_training_instances(
        [input_file], tokenizer, FLAGS.max_seq_length, False, FLAGS.dupe_factor,
        FLAGS.short_seq_prob, FLAGS.masked_lm_prob, FLAGS.max_predictions_per_seq,
        rng))
  for input_file in input_files_synthetic:
    tf.logging.info("  %s", input_file)
    rng = random.Random(FLAGS.random_seed)
    instances.extend(create_training_instances(
        [input_file], tokenizer, FLAGS.max_seq_length, True, FLAGS.dupe_factor,
        FLAGS.short_seq_prob, FLAGS.masked_lm_prob, FLAGS.max_predictions_per_seq,
        rng))
  
  rng.shuffle(instances)
  tf.logging.info("*** Writing to output files ***")
  write_instance_to_example_files(instances, tokenizer, FLAGS.max_seq_length,
                                    FLAGS.max_predictions_per_seq, FLAGS.output_file)
  # output_files = FLAGS.output_file.split(",")
  # n_output_files = []
  # for output_file in output_files:
  #   n_output_files.append(f"{output_file}-shard-{shard_count}")
  #   tf.logging.info("  %s", output_file)

    
  #   shard_count+=1
 
  #   output_files = FLAGS.output_file.split(",")
  #   n_output_files = []
  #   tf.logging.info("*** Writing to output files ***")
  #   for output_file in output_files:
  #     n_output_files.append(f"{output_file}-shard-{shard_count}")
  #     tf.logging.info("  %s", output_file)

  #   write_instance_to_example_files(instances, tokenizer, FLAGS.max_seq_length,
  #                                   FLAGS.max_predictions_per_seq, n_output_files)
  #   shard_count+=1

if __name__ == "__main__":
  flags.mark_flag_as_required("input_file_synthetic")
  flags.mark_flag_as_required("input_file_organic")
  flags.mark_flag_as_required("output_file")
  tf.app.run()
