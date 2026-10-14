"""
Train the Crop Doctor classifier on your own labeled dataset.

Expected folder layout (standard PlantVillage-style):

    data/train/<class_name>/*.jpg
    data/val/<class_name>/*.jpg

<class_name> folders should match the keys in data/disease_info.json,
e.g. "Apple___Apple_scab", "Tomato___healthy", etc. so the app can look
up treatment info for whatever the model predicts.

Usage:
    python train_model.py --epochs 10 --data-dir data

Produces:
    model/crop_doctor_model.keras
    model/class_indices.json
"""
import os
import json
import argparse

from config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.path.join(Config.BASE_DIR, "data"))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--fine-tune-epochs", type=int, default=5,
                         help="Extra epochs unfreezing the top of the backbone.")
    args = parser.parse_args()

    train_dir = os.path.join(args.data_dir, "train")
    val_dir = os.path.join(args.data_dir, "val")

    if not os.path.isdir(train_dir) or not os.path.isdir(val_dir):
        raise SystemExit(
            f"Expected {train_dir} and {val_dir} to exist, each containing one "
            "subfolder per class. See the docstring at the top of this file."
        )

    import tensorflow as tf
    from tensorflow.keras import layers, models

    img_size = Config.IMG_SIZE
    batch_size = args.batch_size

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir, image_size=img_size, batch_size=batch_size, label_mode="categorical"
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir, image_size=img_size, batch_size=batch_size, label_mode="categorical"
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Found {num_classes} classes: {class_names[:5]}{'...' if num_classes > 5 else ''}")

    os.makedirs(os.path.dirname(Config.CLASS_INDEX_PATH), exist_ok=True)
    with open(Config.CLASS_INDEX_PATH, "w") as f:
        json.dump({name: i for i, name in enumerate(class_names)}, f, indent=2)

    normalize = layers.Rescaling(1.0 / 255)
    augment = models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ])

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.map(lambda x, y: (augment(normalize(x), training=True), y)).prefetch(autotune)
    val_ds = val_ds.map(lambda x, y: (normalize(x), y)).prefetch(autotune)

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=img_size + (3,), include_top=False, weights="imagenet"
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=img_size + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    model.summary()

    print("\n--- Phase 1: training the classification head ---")
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs)

    if args.fine_tune_epochs > 0:
        print("\n--- Phase 2: fine-tuning the top of the backbone ---")
        base_model.trainable = True
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-5),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        model.fit(train_ds, validation_data=val_ds, epochs=args.fine_tune_epochs)

    os.makedirs(os.path.dirname(Config.MODEL_PATH), exist_ok=True)
    model.save(Config.MODEL_PATH)
    print(f"\nSaved model to {Config.MODEL_PATH}")
    print(f"Saved class index to {Config.CLASS_INDEX_PATH}")


if __name__ == "__main__":
    main()
