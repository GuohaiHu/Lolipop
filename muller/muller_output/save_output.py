import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas

# logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
ROOT_GENOTYPE_LABEL = "genotype-0"
FILTERED_GENOTYPE_LABEL = "removed"
OutputType = Tuple[pandas.DataFrame, pandas.DataFrame, str, Dict[str, Any]]

try:
	from muller.clustering.generatelegacy import GenotypeOptions
	from clustering.metrics.pairwise_calculation_cache import PairwiseCalculationCache
	from inheritance.sort_genotypes import SortOptions
	from inheritance.order import OrderClusterParameters
	from graphics import plot_genotypes, plot_heatmap, plot_dendrogram, generate_muller_plot, plot_timeseries
	from muller.muller_output.generate_tables import *
	from muller.muller_output.generate_scripts import generate_r_script, execute_r_script
	from muller import widgets, dataio, palettes
	from muller.muller_output.flowchart import flowchart
except ModuleNotFoundError:
	from clustering.metrics.pairwise_calculation_cache import PairwiseCalculationCache
	from graphics import plot_genotypes, plot_heatmap, plot_dendrogram, generate_muller_plot, plot_timeseries
	from muller_output.generate_tables import *
	from muller_output.generate_scripts import generate_r_script, execute_r_script
	import widgets
	import palettes
	import dataio
	from muller_output.flowchart import flowchart

	GenotypeOptions = Any
	SortOptions = Any
	OrderClusterParameters = Any


@dataclass
class WorkflowData:
	# Used to organize the output from the workflow.
	filename: Path
	program_options: Any
	info: Optional[pandas.DataFrame]
	original_trajectories: Optional[pandas.DataFrame]
	original_genotypes: Optional[pandas.DataFrame]
	trajectories: pandas.DataFrame
	genotypes: pandas.DataFrame
	genotype_members: pandas.Series
	clusters: Any
	genotype_options: GenotypeOptions
	sort_options: SortOptions
	cluster_options: OrderClusterParameters
	p_values: PairwiseCalculationCache
	filter_cache: List[Tuple[pandas.DataFrame, pandas.DataFrame]]
	linkage_matrix: Any
	genotype_palette_filename: Optional[Path]


class OutputFilenames:
	""" Used to organize the files generated by the workflow.
	"""

	def __init__(self, output_folder: Path, name: str, suffix = 'tsv'):
		self.suffix = suffix

		def check_folder(path: Union[str, Path]) -> Path:
			path = Path(path)
			if not path.exists():
				path.mkdir()
			return path.absolute()

		output_folder = check_folder(output_folder)
		supplementary_folder = check_folder(output_folder / "supplementary-files")
		graphics_folder = check_folder(output_folder / "graphics")
		graphics_distinctive_folder = check_folder(graphics_folder / "distinctive")
		graphics_clade_folder = check_folder(graphics_folder / "clade")
		tables_folder = check_folder(output_folder / "tables")
		scripts_folder = check_folder(output_folder / "scripts")

		# General Files
		self.trajectory: Path = output_folder / (name + f'.trajectories.{suffix}')
		self.genotype: Path = output_folder / (name + f'.muller_genotypes.{suffix}')
		self.muller_plot_annotated: Path = output_folder / (name + '.muller.annotated.png')

		# tables
		self.original_trajectory: Path = tables_folder / (name + f'.trajectories.original.{suffix}')
		self.original_genotype: Path = tables_folder / (name + f'.muller_genotypes.original.{suffix}')
		self.population: Path = tables_folder / (name + f'.ggmuller.populations.{suffix}')
		self.edges: Path = tables_folder / (name + f'.ggmuller.edges.{suffix}')
		self.muller_table: Path = tables_folder / (name + f'.muller.csv')  # This is generated in r.

		self.linkage_matrix_table = tables_folder / (name + f".linkagematrix.tsv")
		self.distance_table: Path = tables_folder / (name + ".distance.tsv")
		self.distance_matrix: Path = tables_folder / (name + f".distance.{suffix}")

		# graphics
		## Muller Plots
		self.muller_plot_unannotated: Path = graphics_distinctive_folder / (name + '.muller.unannotated.png')
		self.muller_plot_annotated_pdf: Path = graphics_clade_folder / (name + '.muller.annotated.pdf')
		self.muller_plot_annotated_svg: Path = graphics_clade_folder / (name + ".muller.annotated.svg")
		self.muller_plot_basic: Path = graphics_clade_folder / (name + '.muller.basic.png')
		self.muller_plot_annotated_distinctive: Path = graphics_distinctive_folder / (name + '.muller.annotated.distinctive.png')
		self.muller_plot_annotated_distinctive_svg: Path = graphics_distinctive_folder / (name + '.muller.annotated.distinctive.svg')

		##Timeseries plots
		self.genotype_plot: Path = graphics_distinctive_folder / (name + '.genotypes.distinctive.png')
		self.trajectory_plot_distinctive: Path = graphics_distinctive_folder / (name + f".trajectories.distinctive.png")
		self.genotype_plot_filtered: Path = output_folder / (name + f".genotypes.filtered.png")

		## Geneology plots
		self.lineage_render: Path = output_folder / (name + '.geneology.svg')
		self.lineage_image_clade: Path = graphics_distinctive_folder / (name + f".geneology.distinctive.png")
		self.lineage_image_distinct: Path = output_folder / (name + '.geneology.png')

		## Other plots
		self.distance_heatmap: Path = graphics_folder / (name + f".heatmap.distance.png")
		self.linkage_plot = graphics_folder / (name + f".dendrogram.png")

		# scripts
		self.r_script: Path = scripts_folder / (name + '.r')
		self.mermaid_script: Path = scripts_folder / (name + '.mermaid.md')

		# supplementary files
		self.parameters: Path = supplementary_folder / (name + '.json')

	@property
	def delimiter(self) -> str:
		if self.suffix == 'tsv':
			return '\t'
		else:
			return ','


def get_workflow_parameters(workflow_data: WorkflowData, genotype_colors = Dict[str, str]) -> Dict[str, float]:
	options = {k: (v if not isinstance(v, Path) else str(v)) for k, v in workflow_data.program_options.items()}
	parameters = {
		# get_genotype_options
		'detectionCutoff':                        workflow_data.genotype_options.detection_breakpoint,
		'fixedCutoff':                            workflow_data.genotype_options.fixed_breakpoint,
		'similarityCutoff':                       workflow_data.genotype_options.similarity_breakpoint,
		'differenceCutoff':                       workflow_data.genotype_options.difference_breakpoint,
		# sort options
		'significanceCutoff':                     workflow_data.sort_options.significant_breakpoint,
		'frequencyCutoffs':                       workflow_data.sort_options.frequency_breakpoints,
		# cluster options
		'additiveBackgroundDoubleCheckCutoff':    workflow_data.cluster_options.additive_background_double_cutoff,
		'additiveBackgroundSingleCheckCutoff':    workflow_data.cluster_options.additive_background_single_cutoff,
		'subtractiveBackgroundDoubleCheckCutoff': workflow_data.cluster_options.subtractive_background_double_cutoff,
		'subtractiveBackgroundSingleCheckCutoff': workflow_data.cluster_options.subtractive_background_single_cutoff,
		'derivativeDetectionCutoff':              workflow_data.cluster_options.derivative_detection_cutoff,
		'derivativeCheckCutoff':                  workflow_data.cluster_options.derivative_check_cutoff,
		# Palette
		'genotypePalette':                        genotype_colors,
		'commit':                                 widgets.get_commit_hash(),
		'method':                                 workflow_data.genotype_options.method,
		'metric':                                 workflow_data.genotype_options.metric,
		'options':                                options
	}
	return parameters


def generate_output(workflow_data: WorkflowData, output_folder: Path, detection_cutoff: float, adjust_populations: bool):
	# Set up the output folder
	base_filename = workflow_data.filename.stem
	if workflow_data.program_options['sheetname'] and workflow_data.program_options['sheetname'] != 'Sheet1':
		base_filename += '.' + workflow_data.program_options['sheetname']

	filenames = OutputFilenames(output_folder, base_filename)
	delimiter = filenames.delimiter

	# Map each trajectory to its parent genotype.
	parent_genotypes = widgets.map_trajectories_to_genotype(workflow_data.genotype_members)

	##############################################################################################################################################
	# ------------------------------------------- Save the genotype and trajectory tables --------------------------------------------------------
	##############################################################################################################################################

	workflow_data.genotypes.to_csv(str(filenames.genotype), sep = delimiter)

	print("Saving Trajectory Tables...")
	# Save trajectory tables, if available
	if workflow_data.trajectories is not None:
		filtered_trajectories = generate_missing_trajectories_table(workflow_data.trajectories, workflow_data.original_trajectories)
		trajectories = generate_trajectory_table(workflow_data.trajectories, parent_genotypes, workflow_data.info)
		trajectories.to_csv(str(filenames.trajectory), sep = delimiter)

	##############################################################################################################################################
	# ----------------------------------------- # Generate the input tables to ggmuller ----------------------------------------------------------
	##############################################################################################################################################
	edges_table = workflow_data.clusters.as_ancestry_table().reset_index()
	edges_table = edges_table[['Parent', 'Identity']]  # Otherwise the r script doesn't work.
	population_table = generate_ggmuller_population_table(workflow_data.genotypes, edges_table, detection_cutoff, adjust_populations)
	population_table.to_csv(str(filenames.population), sep = delimiter, index = False)
	edges_table.to_csv(str(filenames.edges), sep = delimiter, index = False)
	##############################################################################################################################################
	# ----------------------------------------- Generate the palette for the praphics ------------------------------------------------------------
	##############################################################################################################################################
	_all_genotype_labels = sorted(set(list(workflow_data.original_genotypes.index) + list(workflow_data.genotypes.index)))
	# Annotations may be used to select specific colors for the lineage palette.
	genotype_annotations = dataio.parse_genotype_annotations(
		workflow_data.genotype_members,
		workflow_data.info,
		workflow_data.program_options['alias_filename']
	)
	# The custom palette overrides any other color.
	if workflow_data.genotype_palette_filename:
		custom_palette = dataio.read_map(workflow_data.genotype_palette_filename)
	else:
		custom_palette = {}

	genotype_colors_distinct = palettes.generate_palette(_all_genotype_labels)
	genotype_colors_clade = palettes.generate_palette(edges_table, custom_palette, genotype_annotations, 'lineage')

	##############################################################################################################################################
	# ------------------------------------------------- Save supplementary files -----------------------------------------------------------------
	##############################################################################################################################################
	parameters = get_workflow_parameters(workflow_data, genotype_colors_clade)
	filenames.parameters.write_text(json.dumps(parameters, indent = 2))

	# Generate and excecute scripts
	##############################################################################################################################################
	# ------------------------------------------------- Generate the lineage plots ---------------------------------------------------------------
	##############################################################################################################################################
	print("Generating Lineage Plots...")
	flowchart(edges_table, genotype_colors_clade, annotations = genotype_annotations, filename = filenames.lineage_image_distinct)
	flowchart(edges_table, genotype_colors_distinct, annotations = genotype_annotations, filename = filenames.lineage_render)
	flowchart(edges_table, genotype_colors_distinct, annotations = genotype_annotations, filename = filenames.lineage_image_clade)

	##############################################################################################################################################
	# ------------------------------------------------- Generate and excecute the r script -------------------------------------------------------
	##############################################################################################################################################
	muller_df = generate_r_script(
		trajectory = filenames.trajectory,
		population = filenames.population,
		edges = filenames.edges,
		table_filename = filenames.muller_table,
		plot_filename = filenames.muller_plot_basic,
		script_filename = filenames.r_script,
		color_palette = genotype_colors_clade,
		genotype_labels = population_table['Identity'].unique().tolist()
	)

	# Generate time series plots showing the mutations/genotypes over time.

	##############################################################################################################################################
	# -------------------------------- Generate time series plots showing the mutations/genotypes over time --------------------------------------
	##############################################################################################################################################
	print("Generating series plots...")
	trajectory_colors_distinct = {k: genotype_colors_distinct[v] for k, v in parent_genotypes.items()}
	trajectory_colors_lineage = {k: genotype_colors_clade[v] for k, v in parent_genotypes.items()}

	plot_genotypes(workflow_data.trajectories, workflow_data.genotypes, filenames.genotype_plot, genotype_colors_distinct, trajectory_colors_distinct)
	if workflow_data.trajectories is not None:
		plot_timeseries(workflow_data.trajectories, trajectory_colors_distinct, filename = filenames.trajectory_plot_distinctive)
		plot_genotypes(filtered_trajectories, workflow_data.genotypes, filenames.genotype_plot_filtered, genotype_colors_clade,
			trajectory_colors_lineage)

	##############################################################################################################################################
	# ------------------------------------- Generate the muller plot using the table from the r script -------------------------------------------
	##############################################################################################################################################
	print("Generating muller plots...")
	if muller_df is not None:
		annotated_muller_plot_filenames = [
			filenames.muller_plot_annotated,
			filenames.muller_plot_annotated_pdf,
			filenames.muller_plot_annotated_svg
		]
		distinctive_muller_plot_filenames = [
			filenames.muller_plot_annotated_distinctive,
			filenames.muller_plot_annotated_distinctive_svg
		]
		generate_muller_plot(muller_df, genotype_colors_clade, annotated_muller_plot_filenames, genotype_annotations)
		generate_muller_plot(muller_df, genotype_colors_distinct, distinctive_muller_plot_filenames)

	##############################################################################################################################################
	# -------------------------------------------------- Generate supplementary graphics ---------------------------------------------------------
	##############################################################################################################################################

	if workflow_data.linkage_matrix is not None:
		num_trajectories = len(workflow_data.trajectories)
		linkage_table = widgets.format_linkage_matrix(workflow_data.linkage_matrix, num_trajectories)
		linkage_table.to_csv(str(filenames.linkage_matrix_table), sep = delimiter, index = False)
		try:
			plot_dendrogram(workflow_data.linkage_matrix, workflow_data.p_values, filenames.linkage_plot)
		except:
			pass
	workflow_data.p_values.save(filenames.distance_table)

	try:
		squareform = workflow_data.p_values.squareform()
		squareform.to_csv(filenames.distance_matrix)
	except:
		pass

	pvalues_matrix = workflow_data.p_values.squareform()
	try:
		plot_heatmap(pvalues_matrix, filenames.distance_heatmap)
	except:
		pass
