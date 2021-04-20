nextflow.enable.dsl=2

import java.nio.file.Paths

moduleName="plotting"
binDir = Paths.get(workflow.projectDir.toString(), "src/$moduleName/bin/")

process plot_decoded_spots {
    publishDir "$params.outDir/plots", mode: 'copy'

    input:
    path decoded_genes
    path reference_image
    val grid_size_x
    val grid_size_y
    val tile_size_x
    val tile_size_y
    

    output:
    path "decoded_genes_plotted.pdf"
    path "decoded_genes_plotted-1.png"
    script:

    """
    python $binDir/plotDecodedGenes.py $reference_image $decoded_genes $grid_size_x,$grid_size_y $tile_size_x $tile_size_y
    pdftoppm -png -r 300 decoded_genes_plotted.pdf decoded_genes_plotted
    """
}
process plot_detected_spots {
    publishDir "$params.outDir/plots", mode: 'copy'

    input:
    path detected_spots
    val grid_size_x
    val grid_size_y
    val tile_size_x
    val tile_size_y
    

    output:
    path "detected_spots_plotted.pdf"
    path "detected_spots_plotted-1.png"
    script:

    """
    python $binDir/plotDetectedSpots.py $detected_spots $grid_size_x,$grid_size_y $tile_size_x $tile_size_y
    pdftoppm -png -r 300 detected_spots_plotted.pdf detected_spots_plotted
    """
}
process plot_segmentation_labels {
    publishDir "$params.outDir/plots/segmentation/", mode: 'copy'

    input:
    tuple val(tile_nr), path(labeled_image),path(original_image)
    output:
    path "${labeled_image.baseName}_overlay_DAPI.tif"

    script:

    """
    python $binDir/plotLabeledImages.py $labeled_image $original_image 
    """
}
