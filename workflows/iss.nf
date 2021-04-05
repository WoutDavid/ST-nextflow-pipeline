nextflow.enable.dsl=2

///////////////////////
// Include processes:
///////////////////////


include {
    standard_iss_tiling as tiling;
} from "../src/tiling/workflows/tiling_workflows.nf"


include {
    global_rigid_register as global_register;
} from "../src/registration/processes/global_registration.nf"

workflow iss {
    
    take:
        data
    main:
        /*
        Example of an optional step:
        if(params.sc.scanpy.containsKey("filter")) {
            out = QC_FILTER( out ).filtered // Remove concat
        }
        */
        global_register(data)
        global_register.out.view()

}