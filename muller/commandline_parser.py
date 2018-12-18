import argparse
import itertools
import math
from pathlib import Path
from typing import List, Optional, Union

from dataclasses import dataclass


# For convienience. Helps with autocomplete.
@dataclass
class ProgramOptions:
	filename: Path
	output_folder: Path
	sheetname: str = "Sheet1"
	fixed_breakpoint: Optional[float] = None
	detection_breakpoint: float = 0.03
	significant_breakpoint: float = 0.15
	mode: bool = False
	frequencies: List[float] = 0.10
	similarity_breakpoint: float = 0.05
	difference_breakpoint: float = 0.10
	is_genotype: bool = False
	use_filter: bool = True
	annotate_all: bool = False
	save_pvalue: bool = True
	use_strict_filter: bool = False

	def __post_init__(self):
		if self.output_folder and not self.output_folder.exists():
			sup = self.output_folder / "supplementary-files"
			self.output_folder.mkdir()

			if not sup.exists():
				sup.mkdir()

	@classmethod
	def from_parser(cls, parser: Union['ProgramOptions', argparse.Namespace]) -> 'ProgramOptions':
		filename = Path.cwd() / parser.filename
		output_folder = Path.cwd() / parser.output_folder

		fixed = parser.fixed_breakpoint
		if fixed is None:
			fixed = 1 - float(parser.detection_breakpoint)
		else:
			fixed = float(fixed)

		frequencies = _parse_frequency_option(parser.frequencies)

		return cls(
			filename = filename,
			output_folder = output_folder,
			sheetname = parser.sheetname,
			fixed_breakpoint = fixed,
			detection_breakpoint = float(parser.detection_breakpoint),
			significant_breakpoint = float(parser.significant_breakpoint),
			mode = parser.mode,
			frequencies = frequencies,
			similarity_breakpoint = float(parser.similarity_breakpoint),
			difference_breakpoint = float(parser.difference_breakpoint),
			is_genotype = parser.is_genotype,
			use_filter = parser.use_filter,
			annotate_all = parser.annotate_all,
			save_pvalue = parser.save_pvalue,
			use_strict_filter = parser.use_strict_filter
		)

	@classmethod
	def debug(cls, parser) -> 'ProgramOptions':
		parser.filename = "/home/cld100/Documents/github/muller_diagrams/tests/data/B1_Muller.xlsx"
		parser.output_folder = './output'
		parser.use_filter = True
		return cls.from_parser(parser)


def _parse_frequency_option(frequency: Union[str, List[float]]) -> List[float]:
	if isinstance(frequency, str):
		if ',' in frequency:
			frequencies = list(map(float, frequency.split(',')))
		else:
			frequencies = float(frequency)
	elif isinstance(frequency, float):
		frequencies = frequency
	else:
		frequencies = [float(i) for i in frequency]
	if isinstance(frequencies, float):
		frequencies = [math.fsum(itertools.repeat(frequencies, i)) for i in range(int(1 / frequencies) + 1)]
		frequencies = [round(i, 2) for i in frequencies]
	if 0 not in frequencies:
		frequencies = [0] + frequencies
	frequencies = sorted(frequencies, reverse = True)
	return frequencies


def create_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description = "Generates muller diagrams based on a set of mutational trajectories.",
		formatter_class = argparse.ArgumentDefaultsHelpFormatter
	)
	parser.add_argument(
		'-i', '--input',
		help = "The table of trajectories to cluster.",
		action = 'store',
		dest = 'filename',
		type = Path
	)
	parser.add_argument(
		"--sheetname",
		help = "Indicates the sheet to use if the input table is an excel workbook and the data is not in Sheet1",
		action = 'store',
		dest = 'sheetname',
		default = 'Sheet1',
		type = str
	)
	parser.add_argument(
		'-o', '--output',
		help = "The folder to save the files to.",
		action = 'store',
		dest = 'output_folder',
		type = Path
	)
	parser.add_argument(
		'--fixed',
		help = "The minimum frequency at which to consider a mutation fixed.",
		action = 'store',
		dest = 'fixed_breakpoint',
		type = float
	)
	parser.add_argument(
		"-u", "--uncertainty",
		help = "The uncertainty to apply when performing frequency-based calculations. \
			For example, a frequency at a given timepoint is considered undetected if it falls below 0 + `uncertainty`.",
		action = 'store',
		default = 0.03,
		dest = 'detection_breakpoint',
		type = float
	)
	parser.add_argument(
		"-s", "--significant",
		help = "The frequency at which to consider a genotype significantly greater than zero.",
		action = 'store',
		default = 0.15,
		dest = "significant_breakpoint",
		type = float
	)
	parser.add_argument(
		"--matlab",
		help = "Mimics the output of the original matlab script.",
		action = 'store_true',
		dest = "mode"
	)
	parser.add_argument(
		"-f", "--frequencies",
		help = 'The frequency cutoff to use when sorting the muller_genotypes by first detected frequency. For example, a value of 0.15 will use the frequencies 0,.15,.30,.45...',
		action = 'store',
		dest = 'frequencies',
		default = 0.10,
		type = float
	)
	parser.add_argument(
		"-r", "--similarity-cutoff",
		help = "Maximum p-value difference to consider trajectories related. Used when grouping trajectories into muller_genotypes.",
		action = "store",
		default = 0.05,
		dest = "similarity_breakpoint",
		type = float
	)

	parser.add_argument(
		"-l", "--difference-cutoff",
		help = "Minimum p-value to consider a pair of muller_genotypes unrelated. Used when splitting muller_genotypes.",
		action = "store",
		default = 0.25,
		dest = "difference_breakpoint"
	)
	parser.add_argument(
		"--genotypes", "--cohorts",
		help = "Indicates that the input table contains muller_genotypes rather than trajectories.",
		action = 'store_true',
		dest = 'is_genotype'
	)
	parser.add_argument(
		"--no-filter",
		help = "Disables genotype filtering.",
		action = 'store_false',
		dest = 'use_filter'
	)
	parser.add_argument(
		"--annotate-all",
		help = "Adds all gene labels to the muller plots, instead of the top three.",
		action = "store_true",
		dest = "annotate_all"
	)
	parser.add_argument(
		"--save-pvalues",
		help = "Saves the p-values to a table and generates a heatmap for the population. Disabling saves a large amount of time for large datasets.",
		action = "store_true",
		dest = "save_pvalue"
	)
	parser.add_argument(
		"--strict-filter",
		help = "",
		action = "store_true",
		dest = "use_strict_filter"
	)

	return parser
