nextflow.enable.dsl=2

include {
    spot_detection_reference;spot_detection_round ; gather_intensities_in_rounds; get_max_intensities_over_channels
} from "../processes/spot_detection.nf"

include {
    plot_spots_whole_and_on_tiles
} from "$baseDir/src/plotting/workflows/detected_spots_workflow.nf" 


workflow spot_detection_iss {
    take:
    // Data
    reference //Preferably filtered by a filtering method: spot detection will be performed on this
    round_images //the detected spot's intensity will be measured on these images

    // Plotting parameter
    grid_size_x
    grid_size_y
    tile_size_x
    tile_size_y

    main:
    //detect spots on reference image
    spot_detection_reference(reference)

    // This is for spot detection quality control purposes
    /* spot_detection_round(round_images) */
    /* spot_detection_round.out.collectFile(name: "$params.outDir/hybs/concat_hybs.csv", sort:true, keepHeader:true).set {hybs} */

    // Collect all spots in a seperate file
    spot_detection_reference.out.collectFile(name: "$params.outDir/blobs/concat_blobs.csv", sort:true, keepHeader:true).set {blobs}
    blobs_value_channel = blobs.first() //Call first to convert it into a value channel to allow for multiple iteration of a process with multiple inputs

    // Plot all detected spots
    plot_spots_whole_and_on_tiles(spot_detection_reference.out, blobs, reference, grid_size_x,grid_size_y, tile_size_x, tile_size_y)
    
    //map round images into a tuple containing their round, channel and tile number, gather intensity code requires this information up front
    round_images.map {file -> tuple((file.baseName=~ /tiled_\d+/)[0],(file.baseName=~ /Round\d+/)[0],(file.baseName=~ /c\d+/)[0], file) }.set {round_images_mapped}

    // Gather intesnity on each round image of every spot
    gather_intensities_in_rounds(blobs_value_channel, round_images_mapped)
    // Collect all data into one file for downstream analysis
    gather_intensities_in_rounds.out.collectFile(name: "$params.outDir/intensities/concat_intensities.csv", sort:true, keepHeader:true).set {intensities}
    intensities_value_channel = intensities.first()

    get_max_intensities_over_channels(intensities_value_channel) 
    get_max_intensities_over_channels.out.view()
    


    emit:
        get_max_intensities_over_channels.out.flatten()


}
