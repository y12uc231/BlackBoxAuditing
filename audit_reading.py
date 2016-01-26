import matplotlib.pyplot as plt
import json
import os
import random
import csv

def load_audit_confusion_matrices(filename):
  with open(filename) as audit_file:
    audit_file.next() # Skip the first line.

    # Extract the confusion matrices and repair levels from the audit file.
    confusion_matrices = []
    for line in audit_file:
      separator = ":"
      separator_index = line.index(separator)

      repair_level = float(line[:separator_index])
      raw_confusion_matrix = line[separator_index + len(separator):-1]
      confusion_matrix = json.loads( raw_confusion_matrix.replace("'","\"") )
      confusion_matrices.append( (repair_level, confusion_matrix) )

  # Sort the repair levels in case they are out of order for whatever reason.
  confusion_matrices.sort(key = lambda pair: pair[0])
  return confusion_matrices


def graph_audit(filename, measurers, output_image_file):
  with open(filename) as audit_file:
    header_line = audit_file.readline()[:-1] # Remove the trailing endline.

  confusion_matrices = load_audit_confusion_matrices(filename)

  x_axis = [repair_level for repair_level, _ in confusion_matrices]
  y_axes = []

  # Graph the results for each requested measurement.
  for measurer in measurers:
    y_axis = [measurer(matrix) for _, matrix in confusion_matrices]
    plt.plot(x_axis, y_axis, label=measurer.__name__)
    y_axes.append(y_axis)

  # Format and save the graph to an image file.
  plt.title(header_line)
  plt.axis([0,1,0,1.1]) # Make all the plots consistently sized.
  plt.xlabel("Repair Level")
  plt.legend()
  plt.savefig(output_image_file)
  plt.clf() # Clear the entire figure so future plots are empty.

  # Save the data used to generate that image file.
  with open(output_image_file + ".data", "w") as f:
    writer = csv.writer(f)
    headers = ["Repair Level"] + [calc.__name__ for calc in measurers]
    writer.writerow(headers)
    for i, repair_level in enumerate(x_axis):
      writer.writerow([repair_level] + [y_axis[i] for y_axis in y_axes])


def graph_audits(filenames, measurer, output_image_file):
  for filename in filenames:
    with open(filename) as audit_file:
      header_line = audit_file.readline()[:-1] # Remove the trailing endline.
      feature = header_line[header_line.index(":")+1:]

    confusion_matrices = load_audit_confusion_matrices(filename)
    x_axis = [repair_level for repair_level, _ in confusion_matrices]
    y_axis = [measurer(matrix) for _, matrix in confusion_matrices]
    plt.plot(x_axis, y_axis, label=feature)

  # Format and save the graph to an image file.
  plt.title(measurer.__name__)
  plt.axis([0,1,0,1.1]) # Make all the plots consistently sized.
  plt.xlabel("Repair Level")
  plt.legend()
  plt.savefig(output_image_file)
  plt.clf() # Clear the entire figure so future plots are empty.


def rank_audit_files(filenames, measurer):
  scores = []
  for filename in filenames:
    with open(filename) as audit_file:
      header_line = audit_file.readline()[:-1] # Remove the trailing endline.
      feature = header_line[header_line.index(":")+1:]

    confusion_matrices = load_audit_confusion_matrices(filename)
    _, start_matrix = confusion_matrices[0]
    _, end_matrix = confusion_matrices[-1]
    score_difference = measurer(start_matrix)-measurer(end_matrix)
    scores.append( (feature, score_difference) )

  scores.sort(key = lambda score_tup: score_tup[1], reverse=True)
  return scores


def test():
  TMP_DIR = "tmp"
  if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

  test_contents = "GFA Audit for: Test Feature\n0.0:{'A': {'B': 100}, 'B': {'B': 199}}\n0.1:{'A': {'B': 100}, 'B': {'B': 199}}\n0.5:{'A': {'B': 100}, 'B': {'B': 199}}\n1.0:{'A': {'B': 100}, 'B': {'B': 199}}\n"
  test_filenames = [TMP_DIR + "/test_audit_1.audit",
                    TMP_DIR + "/test_audit_2.audit"]

  # Prepare the sample audit files.
  for filename in test_filenames:
    with open(filename, "w") as f:
      f.write(test_contents)

  # A mock measurement measurer that returns a random number.
  def mock_measurer(conf_matrix):
    return random.random()

  # Perform the audit and save it an output image.
  measurers = [mock_measurer, mock_measurer]
  output_image = TMP_DIR + "/test_image.png"
  graph_audit(test_filenames[0], measurers, output_image) # Only need to test 1.

  file_not_empty = os.path.getsize(output_image) > 0
  print "image file generated? --", file_not_empty

  file_not_empty = os.path.getsize(output_image + ".data") > 0
  print "data file generated? --", file_not_empty

  ranked_features = rank_audit_files(test_filenames, mock_measurer)
  print "ranked features sorted? --", ranked_features[0] > ranked_features[1]

  output_image = TMP_DIR + "/test_image2.png"
  graph_audits(test_filenames, mock_measurer, output_image)
  file_not_empty = os.path.getsize(output_image) > 0
  print "ranked image file generated? --", file_not_empty


if __name__=="__main__":
  test()
