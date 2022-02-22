# -*- coding: utf-8 -*-
import pandas as pd
import re

import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
from official.nlp import optimization  # to create AdamW optimizer



def build_classifier_model():
    text_input = tf.keras.layers.Input(shape=(), dtype=tf.string, name='text')
    preprocessing_layer = hub.KerasLayer("https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3", name='preprocessing')
    encoder_inputs = preprocessing_layer(text_input)
    encoder = hub.KerasLayer("https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-4_H-512_A-8/2", trainable=True, name='BERT_encoder')
    outputs = encoder(encoder_inputs)
    net = outputs['pooled_output']
    net = tf.keras.layers.Dropout(0.1)(net)
    net = tf.keras.layers.Dense(1, activation='sigmoid', name='classifier')(net)
    return tf.keras.Model(text_input, net)

tag_remover = re.compile(r'@\w*\s|http\S*')

twit_pd = pd.read_csv("training.1600000.processed.noemoticon.csv", names=["polarity", "id", "date", "query",  " user", "tweet"],encoding="latin_1")
modified_pd = twit_pd.drop(["id", "date", "query",  " user"], axis=1)
modified_pd['tweet'] = modified_pd['tweet'].apply(lambda x: tag_remover.sub("", x))

polarity = modified_pd.pop("polarity")
polarity.replace(4,1, inplace=True)

tweets = tf.convert_to_tensor(modified_pd)
polarity = tf.convert_to_tensor(polarity)

twitter_dataset = tf.data.Dataset.from_tensor_slices((tweets, polarity))
twitter_dataset = twitter_dataset.shuffle(1600000)

total_size = len(twitter_dataset)
train_size = int(total_size*.9)


train_dataset = twitter_dataset.take(train_size)
val_dataset = twitter_dataset.skip(train_size)

AUTOTUNE = tf.data.AUTOTUNE
batch_size = 16

train_dataset = train_dataset.batch(batch_size).cache().prefetch(buffer_size=AUTOTUNE)
val_dataset = val_dataset.batch(batch_size).cache().prefetch(buffer_size=AUTOTUNE)


classifier_model = build_classifier_model()

loss = tf.keras.losses.BinaryCrossentropy()
metrics = tf.metrics.BinaryAccuracy()

epochs = 1
steps_per_epoch = tf.data.experimental.cardinality(train_dataset).numpy()

num_train_steps = steps_per_epoch * epochs
num_warmup_steps = int(0.001*num_train_steps)
init_lr = 3e-5
optimizer = optimization.create_optimizer(init_lr=init_lr,
                                          num_train_steps=num_train_steps,
                                          num_warmup_steps=num_warmup_steps,
                                          optimizer_type='adamw')
classifier_model.compile(optimizer=optimizer,
                         loss=loss,
                         metrics=metrics)

history = classifier_model.fit(x=train_dataset,
                               validation_data=val_dataset,
                               epochs=epochs)

classifier_model.save("bert_sentiment_140_saved_model", include_optimizer=False)