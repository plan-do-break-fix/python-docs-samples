# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# [START ai_platform_tfkeras_task]
"""Trains a Keras model to predict number of trips
started and ended at Citibike stations. """

# [START ai_platform_tfkeras_task_imports]
import argparse
import os

import pandas as pd
import tensorflow as tf

from trainer.tfkeras_model import model
from trainer.tfkeras_model import utils
# [END ai_platform_tfkeras_task_imports]

# [START ai_platform_tfkeras_task_args]
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="path to input data"
    )
    parser.add_argument(
        "--job-dir",
        type=str,
        required=True,
        help="local or GCS location for writing checkpoints and exporting " "models",
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        help="number of times to go through the data, default=20",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="number of records to read during each training step, default=128",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        help="learning rate for gradient descent, default=.01",
    )
    parser.add_argument(
        "--verbosity",
        choices=["DEBUG", "ERROR", "FATAL", "INFO", "WARN"],
        default="INFO",
    )
    return parser.parse_args()
# [END ai_platform_tfkeras_task_args]

# [START ai_platform_tfkeras_task_train_and_evaluate]
# [START ai_platform_tfkeras_task_train_and_evaluate_load]
def train_and_evaluate(input_path, job_dir, num_epochs=5, 
                       batch_size=128, learning_rate=0.01):
    """Trains and evaluates the Keras model.

    Uses the Keras model defined in model.py. Saves the trained model in TensorFlow SavedModel
    format to the path defined in part by the --job-dir argument."""
    
    # Split datasets into training and testing
    train_x, eval_x, train_y, eval_y = utils.load_data(input_path)
# [END ai_platform_tfkeras_task_train_and_evaluate_load]

    # [START ai_platform_tfkeras_task_train_and_evaluate_dimensions]
    # Dimensions
    num_train_examples, input_dim = train_x.shape
    num_eval_examples = eval_x.shape[1]
    # [END ai_platform_tfkeras_task_train_and_evaluate_dimensions]

    # [START ai_platform_tfkeras_task_train_and_evaluate_model]
    # Create the Keras Model
    keras_model = model.create_keras_model(
        input_dim=input_dim,
        output_dim=train_y.shape[1],
        learning_rate=learning_rate,
    )
    # [END ai_platform_tfkeras_task_train_and_evaluate_model]

    # [START ai_platform_tfkeras_task_train_and_evaluate_training_data]
    # Pass a numpy array by passing DataFrame.values
    training_dataset = model.input_fn(
        features=train_x.values,
        labels=train_y.values,
        shuffle=True,
        num_epochs=num_epochs,
        batch_size=batch_size,
    )
    # [END ai_platform_tfkeras_task_train_and_evaluate_training_data]

    # [START ai_platform_tfkeras_task_train_and_evaluate_validation_data]
    # Pass a numpy array by passing DataFrame.values
    validation_dataset = model.input_fn(
        features=eval_x.values,
        labels=eval_y.values,
        shuffle=False,
        num_epochs=num_epochs,
        batch_size=num_eval_examples,
    )
    # [END ai_platform_tfkeras_task_train_and_evaluate_validation_data]

    # [START ai_platform_tfkeras_task_train_and_evaluate_tensorboard]
    # Setup Learning Rate decay.
    lr_decay_cb = tf.keras.callbacks.LearningRateScheduler(
        lambda epoch: learning_rate + 0.02 * (0.5 ** (1 + epoch)), verbose=True
    )

    # Setup TensorBoard callback.
    tensorboard_cb = tf.keras.callbacks.TensorBoard(
        os.path.join(job_dir, "keras_tensorboard"), histogram_freq=1
    )
    # [END ai_platform_tfkeras_task_train_and_evaluate_tensorboard]

    # [START ai_platform_tfkeras_task_train_and_evaluate_fit_export]
    # Train model
    keras_model.fit(
        training_dataset,
        steps_per_epoch=int(num_train_examples / batch_size),
        epochs=num_epochs,
        # validation_data=validation_dataset,
        # validation_steps=1,
        verbose=1,
        callbacks=[lr_decay_cb, tensorboard_cb],
    )

    # Export model
    export_path = os.path.join(job_dir, "tfkeras_model/")
    tf.keras.models.save_model(keras_model, export_path)
    print("Model exported to: {}".format(export_path))
    # [END ai_platform_tfkeras_task_train_and_evaluate_fit_export]

if __name__ == "__main__":
    args = get_args()
    input_path = args.input_path
    job_dir = args.job_dir

    kwargs = {}
    if args.num_epochs:
        kwargs["num-epochs"] = args.num_epochs
    if args.batch_size:
        kwargs["batch-size"] = args.batch_size
    if args.learning_rate:
        kwargs["learning-rate"] = args.learning_rate

    tf.compat.v1.logging.set_verbosity(args.verbosity)

    train_and_evaluate(input_path, job_dir, **kwargs)
# [END ai_platform_tfkeras_task]
