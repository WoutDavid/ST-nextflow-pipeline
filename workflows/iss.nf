nextflow.enable.dsl=2

///////////////////////
// Include processes:
///////////////////////

include {
    iss_round_adder;
} from '../src/utils/workflows/image_name_parser.nf'
include {
    CLIP_AND_RESCALE
} from '../src/normalization/workflows/normalization_workflow.nf'
include {
    standard_iss_tiling as tiling;
} from "../src/tiling/workflows/tiling_workflows.nf"
include {
    create_reference_image
} from "../src/utils/workflows/projections.nf"
include {
    white_tophat_filter
} from "../src/filtering/workflows/filter_workflow.nf"

include {
    local_registration_of_tiles as register 
} from "../src/registration/workflows/local_registration.nf"

include {
    spot_detection_iss as spot_detection;
} from "../src/spot_detection/workflows/spot_detection.nf"

include {
    decode_sequential_max_intensity as decoding
} from "../src/decoding/processes/decoding.nf"

include {
    iss_decoding_statistics
} from "../src/analytics/workflows/decoded_statistics.nf"

include {
    plot_decoded_spots ; plot_detected_spots
} from "../src/plotting/processes/plotting.nf" 



workflow iss {
    main:
        if (!params.containsKey("reference")){
            log.info "No Reference image found, one will be created by taking the maximum intensity projection of the first round."
            //If you even want to remove the round tuple value from this:  rounds.groupTuple(by:0).map {round_nr, files -> files}.first()
            rounds = iss_round_adder()
            params.reference = create_reference_image(rounds.groupTuple(by:0).first()) //Create reference image by taking maxIP on the first round
        }
        // Create the channel of round images, reference is implicitely defined in the config file as params.reference
       rounds = Channel.fromPath("${params.dataDir}/${params.round_prefix}*/${params.round_prefix}*_${params.channel_prefix}*.${params.extension}")

       // // Normalize the round images
       /* rounds = CLIP_AND_RESCALE(rounds) */
       // Perform the complete tiling workflow, including calculating the highest resolution, padded all images to a resolution that would tile all images in equal sizes, registering globally
       tiling("$params.dataDir/$params.round_prefix*/${params.round_prefix}*_${params.channel_prefix}*.$params.extension", rounds, params.reference)
       // Output of this is used often, so we rename the global variables:
       tile_size_x = tiling.out.tile_size_x
       tile_size_y = tiling.out.tile_size_y
       grid_size_x = tiling.out.grid_size_x
       grid_size_y = tiling.out.grid_size_y
       
       //perform white tophat filtering on both reference and round images
       white_tophat_filter(tiling.out.reference,tiling.out.rounds, grid_size_x, grid_size_y, tile_size_x, tile_size_y)

       // Register tiles locally:
       register(white_tophat_filter.out.filtered_ref, white_tophat_filter.out.filtered_round, grid_size_x, grid_size_y, tile_size_x, tile_size_y)

       spot_detection(white_tophat_filter.out.filtered_ref, register.out, grid_size_x, grid_size_y, tile_size_x, tile_size_y)
       
       decoding(spot_detection.out)
       // Pool decoded genes into one file for downstream analysis
       decoding.out.collectFile(name: "$params.outDir/decoded/concat_decoded_genes.csv", sort:true, keepHeader:true).set {decoded_genes}

       iss_decoding_statistics(decoded_genes)
    
       plot_decoded_spots(decoded_genes, tiling.out.padded_whole_reference, grid_size_x, grid_size_y, tile_size_x, tile_size_y)
}
