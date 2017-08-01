from Pegasus.DAX3 import File, Job, Link
from mappings import Inputs, DWIFiles, DWIJobNames


class DWIProcessing(object):
    def __init__(self, dwi_reversed=False, dwi_frmt="mif", mrtrix_thrds="2", dwi_pe_dir="ap"):
        self.dwi_reversed = dwi_reversed
        self.dwi_format = dwi_frmt
        self.mrtrix_threads = mrtrix_thrds
        self.dwi_pe_dir = dwi_pe_dir

    def add_dwi_processing_steps(self, dax):
        # Here we should take from configuration the:
        # DWI format, reversed, AP alg, mrtrix threads

        last_job = None
        dwi_pre_output = None
        dwi_input = File(Inputs.DWI_INPUT.value)
        dwi_conv_output = File(DWIFiles.DWI_RAW_MIF.value)

        if self.dwi_reversed is True:
            job1 = None
            job2 = None

            if self.dwi_format != "mif":
                if self.dwi_format == "dicom":
                    # TODO: is mrconvert interactive for reversed aquisition data? Should we use the next lines?
                    # mrchoose 0 mrconvert $DATA/DWI ./dwi_raw.mif -force
                    # mrchoose 1 mrconvert $DATA/DWI ./dwi_raw_re.mif -force
                    print "Not implemented!"
                else:
                    job1 = Job(DWIJobNames.MRCONVERT.value, node_label="Convert DWI to MIF")
                    job1.addArguments(dwi_input, dwi_conv_output)
                    job1.uses(dwi_input, link=Link.INPUT)
                    job1.uses(dwi_conv_output, link=Link.OUTPUT, transfer=False, register=False)
                    dax.addJob(job1)

                    dwi_re_input = File("dwi_re.nii.gz")
                    dwi_re = File("dwi_re.mif")
                    job2 = Job(DWIJobNames.MRCONVERT.value, node_label="Convert DWI_RE to MIF")
                    job2.addArguments(dwi_re_input, dwi_re)
                    job2.uses(dwi_re_input, link=Link.INPUT)
                    job2.uses(dwi_re, link=Link.OUTPUT, transfer=True, register=False)
                    dax.addJob(job2)

            job3 = Job(DWIJobNames.DWIPREPROC.value, node_label="DWI preprocessing")
            job3.addArguments("ap", dwi_conv_output, dwi_pre_output, "-rpe_pair", dwi_conv_output, dwi_re, "-nthreads",
                              self.mrtrix_threads)
            job3.uses(dwi_conv_output, link=Link.INPUT)
            job3.uses(dwi_re, link=Link.INPUT)
            job3.uses(dwi_pre_output, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job3)

            if job1 is not None:
                dax.depends(job3, job1)

            if job2 is not None:
                dax.depends(job3, job2)

            last_job = job3

        else:
            dwi_conv_output = None
            job1 = None

            if self.dwi_format != "mif":
                job1 = Job(DWIJobNames.MRCONVERT.value, node_label="Convert DWI to MIF")
                job1.addArguments(dwi_input, dwi_conv_output)
                job1.uses(dwi_input, link=Link.INPUT)
                job1.uses(dwi_conv_output, link=Link.OUTPUT, transfer=False, register=False)
                dax.addJob(job1)

            if dwi_conv_output is None:
                dwi_conv_output = dwi_input

            dwi_pre_output = File(DWIFiles.DWI_MIF.value)
            job2 = Job(DWIJobNames.DWIPREPROC.value, node_label="DWI preprocessing")
            job2.addArguments("ap", dwi_conv_output, dwi_pre_output, "-rpe_none", "-nthreads", self.mrtrix_threads)
            job2.uses(dwi_conv_output, link=Link.INPUT)
            job2.uses(dwi_pre_output, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job2)

            if job1 is not None:
                dax.depends(job2, job1)

            last_job = job2

        mask_output = File(DWIFiles.MASK_MIF.value)
        job3 = Job(DWIJobNames.DWI2MASK.value, node_label="Create DWI mask")
        job3.addArguments(dwi_pre_output, mask_output, "-nthreads", self.mrtrix_threads)
        job3.uses(dwi_pre_output, link=Link.INPUT)
        job3.uses(mask_output, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job3)

        dax.depends(job3, last_job)

        b0_output = File(DWIFiles.B0_NII_GZ.value)
        job4 = Job(DWIJobNames.DWIEXTRACT.value, node_label="Extract DWI B0")
        job4.addArguments(dwi_pre_output, b0_output)
        job4.uses(dwi_pre_output, link=Link.INPUT)
        job4.uses(b0_output, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job4)

        dax.depends(job4, last_job)

        return job4, job3