# !/usr/bin/python 
# -*- coding: utf-8 -*-
# Author:lihuiru
# Created on 2023/11/12 19:53
import os
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from joblib import load
from pandas.errors import EmptyDataError
import numpy as np

MAPPING_DICT = {1: 'Virulent', 0: 'Avirulent'}
HA_TYPES = [f"H{i}" for i in range(1, 19) if i != 3]
NA_TYPES = [f"N{i}" for i in range(1, 10) if i != 2]
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATURES_PATH = os.path.join(base_dir, 'model','top_features.joblib')

def transform_df(df):
    # Replace NaN values with False before applying the ~ operator
    # df = df[~df.loc[:, "Virulence Markers"].str.contains("&", na = False)]
    df = df.fillna('')

    # Group by 'Strain ID' and 'Protein Type', then aggregate 'Virulence Markers'
    transformed = df.groupby(['Strain ID', 'Protein Type']).agg({
        # Join each item in the series after stripping '&', if necessary
        'Virulence Markers': lambda x: ','.join(x.astype(str))#.apply(lambda i: i.replace('&', ''))
    }).reset_index()

    # Calculate the count of 'Virulence Markers'
    transformed['Number of Virulence Markers'] = transformed['Virulence Markers'].apply(lambda x: len(x.split(',')))

    # Adding empty columns for 'Sequence Type' since it is not provided in the original data
    transformed['Sequence Type'] = ''

    return transformed


def explode_markers(df, input_marker_path, output_directory, prefix):
    """
    Explode the markers from the CSV file into individual mutations and create a crosstab matrix.

    Parameters:
    - df: A DataFrame for exploding.
    - input_marker_path: Path to the CSV file containing marker data.
    - output_directory: Directory where the output files will be saved.
    - prefix: Prefix for the output filenames.

    Returns:
    - DataFrame with the crosstab matrix of markers.
    """
    # Extract the filename without extension
    input_marker_filename = os.path.basename(input_marker_path).rsplit(".", 1)[0]

    # Read the CSV file into a DataFrame
    df = transform_df(df)
    df_original = df.copy()

    # Group and sum the 'Number of Virulence markers' by 'Strain ID'
    grouped = df.groupby('Strain ID')['Number of Virulence Markers'].sum()

    # Identify strains with no adaptive markers
    mask = df['Strain ID'].map(grouped) == 0
    no_adaptive_marker_count = mask.sum()
    if no_adaptive_marker_count > 0:
        print(f"There are {no_adaptive_marker_count} strains without any markers.")

    # Explode the 'Adaptive markers' column from a comma-separated string into a list
    df['Virulence Markers'] = df['Virulence Markers'].str.split(',')

    # Expand the list into a new DataFrame and merge it back
    df = df.explode('Virulence Markers')

    # Add a new column with mutations and protein types combined
    df['Marker_Protein'] = df['Virulence Markers'] + '_' + df['Protein Type']

    # Create a new DataFrame with columns as possible 'marker_Protein' values, rows as 'Strain ID'
    df_matrix = pd.crosstab(df['Strain ID'], df['Marker_Protein'])

    # Replace counts with 1 (presence) or 0 (absence)
    df_matrix = df_matrix.applymap(lambda x: 1 if x > 0 else 0)

    # Reset index to turn 'Strain ID' into a column
    df_matrix.reset_index(inplace = True)

    # Add labels to the results DataFrame, keeping only strains with adaptive mutations
    df_label = pd.merge(df_matrix, df_original, on = 'Strain ID')

    # Drop duplicates based on 'Strain ID'
    df_label.drop(labels = ['Virulence Markers', 'Number of Virulence Markers', 'Protein Type'], axis = 1,
                  inplace = True)

    df_label.drop_duplicates(subset = "Strain ID", keep = "first", inplace = True)

    output_matrix_filename = f'{output_directory}/{prefix}{input_marker_filename}_matrix.csv'

    if '_' in df_label.columns:
        df_label.drop(columns = ['_'], inplace = True)
    df_label.to_csv(output_matrix_filename, index = False)

    return df_label


def ensemble_predict(ensemble, X_data, threshold = 0.5):
    all_preds = []
    all_probas = []

    for model, features in zip(ensemble['models'], ensemble['feature_sets']):
        valid_features = [f for f in features if f in X_data.columns]
        missing_features = set(features) - set(valid_features)

        if missing_features:
            print(f"Warning: Missing features filled with zeros: {missing_features}")

        X_subset = X_data[valid_features].copy()
        for missing in missing_features:
            X_subset[missing] = 0
        pred = model.predict(X_subset)
        all_preds.append(pred)

        proba = model.predict_proba(X_subset)[:, 1]
        all_probas.append(proba)

    final_proba = np.mean(all_probas, axis = 0)

    y_pred = np.where(final_proba >= threshold, 2, 1)
    return y_pred, final_proba



def get_explode_marker_file(input_marker_path, output_directory = ".", prefix = ""):
    """
       Processes input marker file(s) by exploding the adaptive markers into individual columns
       indicating the presence or absence of each marker in each strain. This function handles
       both individual files and directories containing multiple marker files.

       Parameters:
       - input_marker_path (str/Path): The path to the input marker file or directory.
       - output_directory (str): The directory where the output files will be saved.
       - prefix (str): The prefix to be added to the output filenames.

       Returns:
       - DataFrame: The combined DataFrame of all processed marker files, or the single processed file.
    """
    os.makedirs(output_directory, exist_ok = True)

    if Path(input_marker_path).is_dir():
        all_df = pd.DataFrame()
        for root, _, files in os.walk(input_marker_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.stat(file_path).st_size > 0:
                    try:
                        df = pd.read_csv(file_path)
                        strain_id = filename.split('_markers.csv')[0]
                        if df.empty:
                            df.loc[0, 'Strain ID'] = strain_id
                        all_df = pd.concat([all_df, df])
                    except EmptyDataError:
                        print(f"Skipping empty data file:{file_path}")
                else:
                    print(f"Skipping empty file:{file_path}")
        # result_df = explode_markers(all_df, "combined_markers.csv", output_directory, prefix)
        if not all_df.empty:
            result_df = explode_markers(all_df, "combined_markers.csv", output_directory, prefix)
        else:
            result_df = pd.DataFrame(columns = ['Strain ID'])
            for root, _, files in os.walk(input_marker_path):
                for idx,filename in enumerate(files):
                    strain_id = filename.split('_markers.csv')[0]
                    result_df.loc[idx,'Strain ID'] = strain_id
    elif Path(input_marker_path).is_file():
        df = pd.read_csv(input_marker_path)
        result_df = explode_markers(df, input_marker_path, output_directory, prefix)
    else:
        print(f"Error: {input_marker_path} is not a valid file or directory", file = sys.stderr)
        return None
    return result_df


def predict_new_data(input_marker_path, model_path, threshold, output_directory = ".",
                     prefix = ""):
    """
    Predict class labels for new data using a trained model, threshold, and a set of top features.

    Parameters:
    - input_marker_path (str): Path to the input marker file or directory containing marker files.
    - model_path (str): Path to the saved model file.
    - threshold(str): Probability threshold for model prediction
    - output_directory (str): Directory where the output files will be saved.
    - prefix (str): Prefix for the output filenames.

    Returns:
    - DataFrame: A DataFrame with strain IDs and their predicted class labels.
    """
    # Process the input marker file first
    add_prefix = prefix + "_" if prefix else ""

    processed_data = get_explode_marker_file(input_marker_path, output_directory, add_prefix)
    processed_data.set_index("Strain ID", inplace = True)
    # Load the trained model

    loaded_ensemble = load(model_path)

    # Initialize a DataFrame with all required features filled with zeros
    all_required_features = []
    for feature_set in loaded_ensemble['feature_sets']:
        all_required_features.extend(feature_set)
    all_required_features = list(set(all_required_features))  # Remove duplicates

    # Create a complete DataFrame with all required features
    complete_data = pd.DataFrame(0, index = processed_data.index, columns = all_required_features)

    # Fill in the values we have from processed_data
    for col in processed_data.columns:
        if col in all_required_features:
            complete_data[col] = processed_data[col]

    # Now predict using the ensemble
    y_pred, new_data_proba = ensemble_predict(loaded_ensemble, complete_data)

    # Calculate probability
    vir_probabilities = [round(prob, 3) for prob in new_data_proba]
    avir_probabilities = [round(1 - prob, 3) for prob in new_data_proba]

    # Create DataFrame with prediction results and probabilities
    prediction_results = []
    for i in range(len(new_data_proba)):
        strain_id = complete_data.index[i]
        vir_prob = vir_probabilities[i]
        avir_prob = avir_probabilities[i]

        if vir_prob >= threshold:
            vir = 'Virulent'
            prob = vir_prob
        else:
            vir = 'Avirulent'
            prob = avir_prob

        prediction_results.append({
            'Strain ID': strain_id,
            'Virulence Level': vir,
            'Probability': prob
        })

    # Convert to DataFrame
    prediction_results_df = pd.DataFrame(prediction_results).reset_index(drop = True)

    # Save to CSV
    prediction_results_df.to_csv(f"{output_directory}/{add_prefix}prediction.csv", index = False, encoding = 'utf-8-sig')

    return prediction_results_df


sys.modules['__main__'].ensemble_predict = ensemble_predict
