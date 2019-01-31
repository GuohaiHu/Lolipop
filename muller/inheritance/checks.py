from typing import Any, Optional, Tuple

import pandas


def check_additive_background(left: pandas.Series, right: pandas.Series, double_cutoff: float, single_cutoff: float) -> bool:
	"""
		Want to check if the sum of two genotypes at one or more timepoints is consistently greater than 1.0
	Parameters
	----------
	left, right: pandas.Series
	double_cutoff: float
		Returns True if two or more timepoints sum to a value that exceeds this frequency.
	single_cutoff
		Returns True if one or more timepoints sum to a value that exceeds this frequency.
	Returns
	-------
	bool
	"""
	trajectorysum = right + left
	double_check = (trajectorysum > double_cutoff).sum() > 0  # Implicit conversion from bool to int.
	single_check = (trajectorysum > single_cutoff).sum() > 0
	return double_check or single_check


def check_subtractive_background(left: pandas.Series, right: pandas.Series, double_cutoff: float,
		single_cutoff: float) -> bool:
	"""
		Check if the one genotype is significantly larger than the other.
	Parameters
	----------
	left: pandas.Series
	right: pandas.Series
	double_cutoff: float
	single_cutoff: float

	Returns
	-------

	"""
	# Check if the current genotype is over 15% larger than the other.
	diff_trajectory = -abs(right - left)
	double_diff_trajectory = (diff_trajectory < double_cutoff).sum() > 1
	single_diff_trajectory = (diff_trajectory < single_cutoff).sum() > 0  # implicit conversion from bool to int
	return double_diff_trajectory or single_diff_trajectory


# noinspection PyTypeChecker
def check_derivative_background(left: pandas.Series, right: pandas.Series, detection_cutoff: float) -> float:
	# Look at the first point when both trajectories are non-zero, and observe delta over time.
	# Are derivatives correlated or anti-correlated? If sufficiently correlated, they are on the same background.
	right_trajectory_filtered: pandas.Series = right > detection_cutoff  # All positions > 0.02 will evaluate to True
	left_trajectory_filtered: pandas.Series = left > detection_cutoff
	# Find the points where neither left nor right is zero.
	startpoint = max([right_trajectory_filtered.idxmax(), left_trajectory_filtered.idxmax()])
	endpoint = min([right_trajectory_filtered[::-1].idxmax(), left_trajectory_filtered[::-1].idxmax()])

	# Convert the index labels to their corresponding integer position in the index.
	# Pandas can't use labels to get a slice of a series.
	start_index = left.index.get_loc(startpoint)
	end_index = left.index.get_loc(endpoint)
	# The matlab script uses the difference of the following timepoint versus the curent one,
	# while pandas default behaviour is current timepoint - previous timepoint.
	# Need to indicate difference of following timepoint, and reverse polarity(negative sign)
	right_derivative = right.diff(-1)
	left_derivative = left.diff(-1)

	right_window = right_derivative[start_index:end_index] * -1
	left_window = left_derivative[start_index:end_index] * -1
	delta = left_window.dot(right_window)

	return delta


def apply_genotype_checks(type_trajectory: pandas.Series, test_trajectory: pandas.Series, options: Any) -> Tuple[bool, bool, Optional[float]]:
	""" Applies the three checks to `type_trajectory` and `test_trajectory`."""
	additive_check = check_additive_background(
		left = type_trajectory,
		right = test_trajectory,
		double_cutoff = options.additive_background_double_cutoff,
		single_cutoff = options.additive_background_single_cutoff
	)

	subtractive_check = check_subtractive_background(
		left = type_trajectory,
		right = test_trajectory,
		double_cutoff = options.subtractive_background_double_cutoff,
		single_cutoff = options.subtractive_background_single_cutoff
	)

	if subtractive_check:
		delta = None
	else:
		delta = check_derivative_background(
			left = type_trajectory,
			right = test_trajectory,
			detection_cutoff = options.derivative_detection_cutoff
		)

	return additive_check, subtractive_check, delta
