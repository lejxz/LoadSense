import argparse
import os
import pickle

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error


def build_target(frame: pd.DataFrame) -> pd.Series:
    noise = (frame["stop_index"] % 3) * 0.2
    return 4.5 + frame["stop_index"] * 0.8 + frame["time_of_day"] * 0.06 + frame["traffic_factor"] * 1.9 + frame["count"] * 0.08 + noise


def main():
    parser = argparse.ArgumentParser(description="Train a lightweight ETA model from synthetic occupancy logs")
    parser.add_argument("--input", default=os.path.join("data", "synthetic_occupancy_logs.csv"))
    parser.add_argument("--output", default=os.path.join("cloud", "artifacts", "eta_model.pkl"))
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    frame = frame.copy()
    frame["eta_minutes"] = build_target(frame)

    features = frame[["stop_index", "time_of_day", "traffic_factor", "route"]]
    target = frame["eta_minutes"]

    numeric_features = ["stop_index", "time_of_day", "traffic_factor"]
    categorical_features = ["route"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
        ]
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", GradientBoostingRegressor(random_state=42)),
    ])

    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    mae = mean_absolute_error(y_test, predictions)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "wb") as handle:
        pickle.dump(pipeline, handle)

    print(f"saved ETA model to {args.output}")
    print(f"validation mae: {mae:.2f}")


if __name__ == "__main__":
    main()
