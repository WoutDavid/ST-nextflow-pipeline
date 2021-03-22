params.n_rounds=4
params.n_channels=4
params.n_tiles=4

round = Channel.fromPath("/media/tool/starfish_test_data/ExampleInSituSequencing/Round1/*.TIF", type: 'file')
datasets = Channel
                .fromPath("/media/tool/starfish_test_data/ExampleInSituSequencing/Round1/*.TIF")
                .map { file -> tuple(file.baseName, file) }

params.reference = "/media/tool/starfish_test_data/ExampleInSituSequencing/DO/REF.TIF"
params.transform_path = "/home/nacho/Documents/Code/communISS/image_processing/registration/calculateTransform.py"
params.register_path = "/home/nacho/Documents/Code/communISS/image_processing/registration/rigidRegister.py"


params.tiling_path = "/home/nacho/Documents/Code/communISS/image_processing/tiling_nextflow.py"
params.target_x_reso=500
params.target_y_reso=500

params.filtering_path= "/home/nacho/Documents/Code/communISS/image_processing/filtering.py"

params.spot_detection_path= "/home/nacho/Documents/Code/communISS/image_processing/spotDetection.py"
params.min_sigma = 1
params.max_sigma = 3

process register{
    publishDir "registered", mode: 'symlink'
    //makes sure that if you echo somehting, it doesn't get surpressed

    //pipes the output ALSO into the given dir instead with a symlink. If 
    // publishDir "./transformed/", mode: 'symlink'

    input:
    // val x from numbers
    path image from round

    output:
    path "${image.baseName}_registered.tif" into transforms

    """
    python ${params.register_path} ${params.reference} ${image}
    """

    }

process tile_round {
    publishDir "tiled_round", mode: 'symlink'
    input: 
    path image from transforms

    output: 
    path "${image.baseName}_tiled_*.tif" into tiled
    
    """
    python ${params.tiling_path} ${image} ${params.target_x_reso} ${params.target_y_reso}
    """
}
process tile_ref {
    publishDir "tiled_ref", mode: 'symlink'
    input:
    path image from params.reference

    output:
    path "${image.baseName}_tiled_*.tif" into tiled_ref

    """
    python ${params.tiling_path} ${image} ${params.target_x_reso} ${params.target_y_reso}
    """
}

process filter {
    publishDir "filtered_round", mode: 'symlink'
    input: 
    //flatmap is really important here to make sure all tiles go into a different map.
    path image from tiled.flatten()

    output:
    path "${image.baseName}_filtered.tif" into filtered_images

    """
    python ${params.filtering_path} ${image}
    """
}

process filter_ref {
    publishDir "filtered_ref", mode: 'symlink'

    input:
    path image from tiled_ref.flatten()
    output:
    path "${image.baseName}_filtered.tif" into filtered_ref_images1, filtered_ref_images2, filtered_ref_images3, filtered_ref_images4

    """
    python ${params.filtering_path} ${image}
    """
}



// process combine_channels {
//     input:
//     val chan_nr from (1..n_channels)
//     val tile_nr from (1..n_tiles)
//     path ref_image from filtered_ref_images
//     path chan_image from filtered_images
// }

// process local_registration {
//     echo true
//     input:
//     file image from filtered_images
//     file ref_image from filtered_ref_images

//     // output:
//     // file "local_registered.tif" into locally_registered_images

//     """
//     echo ${image} ${ref_image}
//     """
//     // python ${params.register_path} ${ref_image} ${image}

// }

process spot_detection {
    publishDir "blobs", mode: 'symlink'

    input:
    path image from filtered_images

    output:
    path "*.csv" into blobs

    """
    python ${params.spot_detection_path} ${image} ${params.min_sigma} ${params.max_sigma}
    """
}    



//for local registration with the reference, yo'ure going to have to duplicate the reference channels, because channels can only be used once as input
