params.n_rounds=4
params.n_channels=4
params.n_tiles=4

params.target_x_reso=500
params.target_y_reso=500

params.filter_radius=15

params.min_sigma = 1
params.max_sigma = 10
params.num_sigma = 30
params.threshold=0.01

/**
   min_sigma=1,
   max_sigma=10,
   num_sigma=30,
   threshold=0.01,
   measurement_type='mean'
**/

nextflow.enable.dsl=2

// Prints a nice intro message before running the pipeline
log.info """\
         COMMUNISS PIPELINE   
         =============================
         Data dir: ${params.dataDir}
         Output dir : ${params.outDir}
         # of Rounds : ${params.n_rounds}
         # of Channels : ${params.n_channels}
         """
         .stripIndent()

// process crop_images {

// }
process register{
    publishDir "$params.outDir/registered/", mode: 'symlink'

    input:
    tuple val(round_nr), path(image) 

    output:
    path "${round_nr}_${image.baseName}_registered.tif" 

    """
    python ${params.register_path} ${params.reference} ${image} ${round_nr}
    """

}

process calculate_tile_size{

    input:
    path image
    output:
    env tile_size_x
    env tile_size_y    
    """
    tile_shape=(`python $params.calculateOptimalTileSize_path $image  500 500`)
    tile_size_x=\${tile_shape[0]} ; tile_size_y=\${tile_shape[1]} ;
    """
}

process tile_round {
    publishDir "$params.outDir/tiled_round/", mode: 'symlink'
    input: 
    path image 

    output: 
    path "${image.baseName}_tiled_*.tif"
    
    """
    python ${params.tiling_path} ${image} ${params.target_x_reso} ${params.target_y_reso}
    """
}

process tile_ref {
    publishDir "$params.outDir/tiled_ref/", mode: 'symlink'
    input:
    path image

    output:
    path "${image.baseName}_tiled_*.tif"

    """
    python ${params.tiling_path} ${image} ${params.target_x_reso} ${params.target_y_reso}
    """
}

process filter_round{
    // echo true
    publishDir "$params.outDir/filtered_round/", mode: 'symlink'
    
    input: 
    path image 

    output:
    path "${image.baseName}_filtered.tif"

    script:
    """
    python ${params.filtering_path} ${image} ${params.filter_radius}
    """
}

process filter_ref {
    publishDir "$params.outDir/filtered_ref/", mode: 'symlink'

    input:
    path image 
    output:
    path "${image.baseName}_filtered.tif" 

    """
    python ${params.filtering_path} ${image} ${params.filter_radius}
    """
}

process local_registration {
    publishDir "$params.outDir/local_register/", mode: 'symlink'

    input: 
    tuple val(x), path(ref_image), path(round_image) 

    output:
    path "${round_image.baseName}_registered.tif"

    script:
    """
    python ${params.register_path} ${ref_image} ${round_image}
    """        

}



process spot_detection_reference {
    publishDir "$params.outDir/blobs", mode: 'symlink'

    input:
    tuple val(tile_nr), path(ref_image) 

    output:
    path "${ref_image.baseName}_blobs.csv"

    """
    python ${params.spot_detection_path} ${ref_image} ${tile_nr} ${params.min_sigma} ${params.max_sigma} 
    """
}
process spot_detection_round {
    publishDir "$params.outDir/hybs", mode: 'symlink'

    input:
    tuple val(tile_nr), val(round_nr), val(channel_nr), path(round_image) 

    output:
    path "${round_image.baseName}_hybs.csv"

    """
    python ${params.spot_detection_path} ${round_image} ${tile_nr} ${params.min_sigma} ${params.max_sigma} ${round_nr} ${channel_nr}
    """
}

process gather_intensities {
    publishDir "$params.outDir/intensities", mode: 'symlink'

    input:
    path blobs
    tuple val(tile_nr), val(round_nr), val(channel_nr), path(round_image)

    output:
    path "${round_image.baseName}_intensities.csv"

    """
    python ${params.gather_intensity_path} ${blobs} ${round_image} ${tile_nr} ${round_nr} ${channel_nr}
    """
}



workflow {
    //load data
    rounds = Channel.fromPath("$params.dataDir/Round*/*.TIF", type: 'file').map { file -> tuple((file.parent=~ /Round\d/)[0], file) }
    //register data
    register(rounds) //output = register.out

    //take one tile and calculate the future tile size, which is stored in calculate_tile_size.out[0] and calculate_tile_size.out[1]
    calculate_tile_size(register.out.first()) 
    
    // tile data
    tile_round(register.out)
    tile_ref(params.reference)

    
    //filter with white_tophat
    filter_ref(tile_ref.out.flatten())
    filter_round(tile_round.out.flatten())
    
    //map filtered images to their respective tile
    filter_ref.out.map(){ file -> tuple((file.baseName=~ /tiled_\d/)[0], file) }.set {filtered_ref_images_mapped} 
    filter_round.out.map(){ file -> tuple((file.baseName=~ /tiled_\d/)[0], file) }.set {filtered_round_images_mapped} 

    //combine ref and rounds into a dataobject that allows for local registration per tile
    //TODO It's clear that this mapping is a bottleneck, since nextflow waits until all round images are filtered before going to local registration, and that shouldn't be hapenning
    filtered_ref_images_mapped.combine(filtered_round_images_mapped,by: 0).set { combined_filtered_tiles}
    //register each tile seperately
    local_registration(combined_filtered_tiles)
    
    local_registration.out.map() {file -> tuple((file.baseName=~ /tiled_\d/)[0],(file.baseName=~ /Round\d/)[0],(file.baseName=~ /c\d/)[0], file) }.set {round_images_mapped}
    // round_images_mapped.groupTuple().map() {round, files -> tuple((file.baseName=~ /Round\d/)[0], file) }.set {round_images_mapped} 

    //detect spots on the reference image
    spot_detection_reference(filtered_ref_images_mapped)
    spot_detection_round(round_images_mapped)

    spot_detection_reference.out.collectFile(name: "$params.outDir/blobs/concat_blobs.csv", sort:true, keepHeader:true).set {blobs}
    blobs_value_channel = blobs.first() //Needs to be a value channel to allow it to iterate multiple times in gather_intensities

    // Gather intensities into one big csv that contains all
    gather_intensities(blobs_value_channel, round_images_mapped)
    gather_intensities.out.collectFile(name: "$params.outDir/intensities/concat_intensities.csv", sort:true, keepHeader:true).set {intensities}
    
}
