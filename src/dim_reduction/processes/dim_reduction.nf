nextflow.enable.dsl=2

import java.nio.file.Paths

moduleName="dim_reduction"
binDir = Paths.get(workflow.projectDir.toString(), "src/$moduleName/bin/")


process umap {
    publishDir "$params.outDir/final/", mode: 'copy'


    input:
    path count_matrix
    
    output:
    path "count_matrix_umap.svg"

    script:
    """
    python $binDir/createUmap.py $count_matrix
    """
}
