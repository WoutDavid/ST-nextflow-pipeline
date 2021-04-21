nextflow.enable.dsl=2

params.stitchDir = "filtered"

include{
    filter_ref; filter_round
} from "../processes/filtering.nf"

include{
    stitch_ref_tiles ; stitch_round_tiles
} from "$baseDir/src/utils/processes/stitching.nf"



workflow white_tophat_filter {
    take: 
        // Tile images
        reference_tiles
        round_tiles

        // Tile grid paramters
        tile_grid_size_x
        tile_grid_size_y
        tile_size_x
        tile_size_y
    main: 
       filter_ref(reference_tiles)
       filter_round(round_tiles)

        // stitche the tiles for visualization 
       stitch_ref_tiles(tile_grid_size_x, tile_grid_size_y, tile_size_x, tile_size_y, filter_ref.out.collect())

       filter_round.out.map() {file -> tuple((file.baseName=~ /Round\d+/)[0],(file.baseName=~ /c\d+/)[0], file)} \
                            .groupTuple(by:[0,1]).set {grouped_rounds}
       stitch_round_tiles(tile_grid_size_x, tile_grid_size_y, tile_size_x, tile_size_y,grouped_rounds)

    emit:
        filtered_ref = filter_ref.out.flatten()
        filtered_round = filter_round.out.flatten()
}
