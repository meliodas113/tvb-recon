from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax import AtlasSuffix
from tvb.recon.dax.mappings import CoregFiles, TractsGenFiles, TractsGenJobNames, DWIJobNames, DWIFiles, AsegFiles, \
    Inputs
from tvb.recon.dax.qc_snapshots import QCSnapshots


class TractsGeneration(object):
    def __init__(self, dwi_multi_shell=False, mrtrix_threads="2", strmlns_no="25M", strmlns_sift_no="5M",
                 strmlns_size="250", strmlns_step="0.5", atlas_suffixes=[AtlasSuffix.DEFAULT], os="LINUX"):
        self.dwi_multi_shell = dwi_multi_shell
        self.mrtrix_threads = mrtrix_threads
        self.strmlns_no = strmlns_no
        self.strmlns_sift_no = strmlns_sift_no
        self.strmlns_size = strmlns_size
        self.strmlns_step = strmlns_step
        self.qc_snapshots = QCSnapshots.get_instance()
        self.atlas_suffixes = atlas_suffixes
        self.os = os

    # job_t1_in_d = job12, job_mask = job5, job_aparc_aseg_in_d = job21
    def add_tracts_generation_steps(self, dax, job_t1_in_d, job_mask, jobs_aparc_aseg_in_d, jobs_fs_custom):

        #-------------------------------------------Tractography--------------------------------------------------------

        t1_in_d = File(CoregFiles.T1_IN_D.value)
        file_5tt = File(TractsGenFiles.FILE_5TT_MIF.value)
        job1 = Job(TractsGenJobNames.JOB_5TTGEN.value, node_label="Generate 5tt MIF")
        job1.addArguments(t1_in_d, file_5tt)
        job1.uses(t1_in_d, link=Link.INPUT)
        job1.uses(file_5tt, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job1)

        dax.depends(job1, job_t1_in_d)

        file_gmwmi = File(TractsGenFiles.GMWMI_MIF.value)
        job2 = Job(TractsGenJobNames.JOB_5TT2GMWMI.value, node_label="Extract GMWMI")
        job2.addArguments(file_5tt, file_gmwmi, "-nthreads", self.mrtrix_threads)
        job2.uses(file_5tt, link=Link.INPUT)
        job2.uses(file_gmwmi, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job2)

        dax.depends(job2, job1)

        file_gmwmi_nii_gz = File(TractsGenFiles.GMWMI_NII_GZ.value)
        job_gmwmi_convert = Job(DWIJobNames.MRCONVERT.value)
        job_gmwmi_convert.addArguments(file_gmwmi, file_gmwmi_nii_gz)
        job_gmwmi_convert.uses(file_gmwmi, link=Link.INPUT)
        job_gmwmi_convert.uses(file_gmwmi_nii_gz, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job_gmwmi_convert)

        dax.depends(job_gmwmi_convert, job2)

        self.qc_snapshots.add_2vols_snapshot_step(dax, [job_gmwmi_convert],
                                                  t1_in_d, file_gmwmi_nii_gz, "gmwmi_in_t1_in_d")

        file_5ttvis = File(TractsGenFiles.FILE_5TTVIS_MIF.value)
        job3 = Job(TractsGenJobNames.JOB_5TT2VIS.value, node_label="Generate TT2VIS MIF")
        job3.addArguments(file_5tt, file_5ttvis)
        job3.uses(file_5tt, link=Link.INPUT)
        job3.uses(file_5ttvis, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job3)

        dax.depends(job3, job2)

        dwi_mif = File(DWIFiles.DWI_MIF.value)
        mask_mif = File(DWIFiles.MASK_MIF.value)

        if self.dwi_multi_shell == "True":
            file_RF_WM = File(TractsGenFiles.RF_WM.value)
            file_RF_GM = File(TractsGenFiles.RF_GM.value)
            file_RF_CSF = File(TractsGenFiles.RF_CSF.value)
            file_RF_voxels = File(TractsGenFiles.RF_VOXELS.value)
            job4 = Job(TractsGenJobNames.DWI2RESPONSE_MSMT.value)
            job4.addArguments(dwi_mif, file_5tt, file_RF_WM, file_RF_GM, file_RF_CSF,
                              file_RF_voxels, self.mrtrix_threads)
            job4.uses(dwi_mif, link=Link.INPUT)
            job4.uses(file_5tt, link=Link.INPUT)
            job4.uses(file_RF_WM, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_GM, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_CSF, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_voxels, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job4)

            dax.depends(job4, job3)

            gm_mif = File(DWIFiles.GM_MIF.value)
            csf_mif = File(DWIFiles.CSF_MIF.value)
            file_wm_fod = File(TractsGenFiles.WM_FOD_MIF.value)
            # TODO: does msdwi2fod exist? should we use dwi2fod with the same args?
            job5 = Job(TractsGenJobNames.MSDWI2FOD.value)
            job5.addArguments("msmt_csd", dwi_mif, file_RF_WM, file_wm_fod, file_RF_GM, gm_mif, file_RF_CSF, csf_mif,
                              "-mask", mask_mif, "-nthreads", self.mrtrix_threads)
            job5.uses(dwi_mif, link=Link.INPUT)
            job5.uses(file_RF_WM, link=Link.INPUT)
            job5.uses(file_RF_GM, link=Link.INPUT)
            job5.uses(file_RF_CSF, link=Link.INPUT)
            job5.uses(mask_mif, link=Link.INPUT)
            job5.uses(file_wm_fod, link=Link.OUTPUT, transfer=True, register=False)
            job5.uses(gm_mif, link=Link.OUTPUT, transfer=True, register=False)
            job5.uses(csf_mif, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job5)

            dax.depends(job5, job4)

            last_job = job5

        else:
            file_response = File(TractsGenFiles.RESPONSE_TXT.value)
            job4 = Job(TractsGenJobNames.DWI2RESPONSE.value, node_label="Compute the DWI Response")
            job4.addArguments(dwi_mif, file_response, mask_mif)
            job4.uses(dwi_mif, link=Link.INPUT)
            job4.uses(mask_mif, link=Link.INPUT)
            job4.uses(file_response, link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(job4)

            dax.depends(job4, job_mask)

            file_wm_fod = File(TractsGenFiles.WM_FOD_MIF.value)
            job5 = Job(TractsGenJobNames.DWI2FOD.value, node_label="Obtain WM FOD")
            job5.addArguments("csd", dwi_mif, file_response, file_wm_fod, "-mask", mask_mif,
                              "-nthreads",
                              self.mrtrix_threads)
            job5.uses(dwi_mif, link=Link.INPUT)
            job5.uses(file_response, link=Link.INPUT)
            job5.uses(mask_mif, link=Link.INPUT)
            job5.uses(file_wm_fod, link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(job5)

            dax.depends(job5, job4)

            last_job = job5

        file_strmlns = File(TractsGenFiles.FILE_TCK.value % self.strmlns_no)
        job6 = Job(TractsGenJobNames.TCKGEN.value, node_label="Generate tracts")

        if self.os == "LINUX":
            job6.addArguments(file_wm_fod, file_strmlns, "-select", self.strmlns_no, "-seed_gmwmi", file_gmwmi, "-act",
                              file_5tt, "-seed_unidirectional", "-maxlength", self.strmlns_size, "-step",
                              self.strmlns_step, "-nthreads", self.mrtrix_threads)
        else:
            job6.addArguments(file_wm_fod, file_strmlns, "-number", self.strmlns_no, "-seed_gmwmi", file_gmwmi, "-act",
                              file_5tt, "-unidirectional", "-maxlength", self.strmlns_size, "-step", self.strmlns_step,
                              "-nthreads", self.mrtrix_threads)
        job6.uses(file_wm_fod, link=Link.INPUT)
        job6.uses(file_gmwmi, link=Link.INPUT)
        job6.uses(file_5tt, link=Link.INPUT)
        job6.uses(file_strmlns, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job6)

        dax.depends(job6, last_job)
        dax.depends(job6, job1)

        file_strmlns_sift = File(TractsGenFiles.FILE_SIFT_TCK.value % self.strmlns_sift_no)
        job7 = Job(TractsGenJobNames.TCKSIFT.value, node_label="Tracts SIFT")
        job7.addArguments(file_strmlns, file_wm_fod, file_strmlns_sift, "-term_number", self.strmlns_sift_no, "-act",
                          file_5tt, "-nthreads", self.mrtrix_threads)
        job7.uses(file_strmlns, link=Link.INPUT)
        job7.uses(file_wm_fod, link=Link.INPUT)
        job7.uses(file_5tt, link=Link.INPUT)
        job7.uses(file_strmlns_sift, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job7)

        dax.depends(job7, job6)
        dax.depends(job7, job1)

        b0_nii_gz = File(DWIFiles.B0_NII_GZ.value)
        file_tdi_ends = File(TractsGenFiles.TDI_ENDS_MIF.value)
        job8 = Job(TractsGenJobNames.TCKMAP.value, node_label="TCKMAP")
        job8.addArguments(file_strmlns_sift, file_tdi_ends, "-vox", "1", "-template", b0_nii_gz)
        job8.uses(file_strmlns_sift, link=Link.INPUT)
        job8.uses(b0_nii_gz, link=Link.INPUT)
        job8.uses(file_tdi_ends, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job8)

        dax.depends(job8, job7)

        file_tdi_ends_nii_gz = File(TractsGenFiles.TDI_ENDS_NII_GZ.value)
        job_convert_tdi_ends = Job(DWIJobNames.MRCONVERT.value)
        job_convert_tdi_ends.addArguments(file_tdi_ends, file_tdi_ends_nii_gz)
        job_convert_tdi_ends.uses(file_tdi_ends, link=Link.INPUT)
        job_convert_tdi_ends.uses(file_tdi_ends_nii_gz, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job_convert_tdi_ends)

        dax.depends(job_convert_tdi_ends, job8)

        self.qc_snapshots.add_2vols_snapshot_step(dax, [job_convert_tdi_ends],
                                                  t1_in_d, file_tdi_ends_nii_gz, "tdi_ends_in_t1_in_d")

        #---------------------------------Connectomes generation per atlas----------------------------------------------

        fs_customs = []
        aparc_aseg_in_ds = []
        file_vol_lbls = []
        fs_color_luts = []
        file_aparc_aseg_counts_csvs = []
        file_aparc_aseg_mean_tract_lengths_csvs = []
        jobs9 = []
        jobs10 = []
        jobs11 = []
        for iatlas, atlas_suffix in enumerate(self.atlas_suffixes):

            fs_customs.append(File(AsegFiles.FS_CUSTOM_TXT.value % atlas_suffix))
            aparc_aseg_in_ds.append(File(CoregFiles.APARC_ASEG_IN_D.value % atlas_suffix))
            file_vol_lbls.append(File(TractsGenFiles.VOLUME_LBL_NII_GZ.value % atlas_suffix))
            fs_color_luts.append(File(Inputs.FS_LUT.value))
            jobs9.append(Job(TractsGenJobNames.LABEL_CONVERT.value,
                             node_label="Compute APARC%s+ASEG labeled for tracts" % atlas_suffix))
            jobs9[-1].addArguments(aparc_aseg_in_ds[-1], fs_color_luts[-1], fs_customs[-1], file_vol_lbls[-1])
            jobs9[-1].uses(aparc_aseg_in_ds[-1], link=Link.INPUT)
            jobs9[-1].uses(fs_color_luts[-1], link=Link.INPUT)
            jobs9[-1].uses(fs_customs[-1], link=Link.INPUT)
            jobs9[-1].uses(file_vol_lbls[-1], link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(jobs9[-1])

            dax.depends(jobs9[-1], jobs_fs_custom[iatlas])
            dax.depends(jobs9[-1], jobs_aparc_aseg_in_d[iatlas])

            self.qc_snapshots.add_2vols_snapshot_step(dax, [jobs9[-1]], t1_in_d, file_vol_lbls[-1],
                                                      "vol%s_lbl_in_t1_in_d" % atlas_suffix)

            file_aparc_aseg_counts_csvs.append(File(TractsGenFiles.TRACT_COUNTS.value % atlas_suffix))
            jobs10.append(Job(TractsGenJobNames.TCK2CONNECTOME.value, node_label="Generate weigths %s "% atlas_suffix))
            jobs10[-1].addArguments(file_strmlns_sift, file_vol_lbls[-1], "-assignment_radial_search", "2",
                               file_aparc_aseg_counts_csvs[-1])
            jobs10[-1].uses(file_strmlns_sift, link=Link.INPUT)
            jobs10[-1].uses(file_vol_lbls[-1], link=Link.INPUT)
            jobs10[-1].uses(file_aparc_aseg_counts_csvs[-1], link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(jobs10[-1])

            dax.depends(jobs10[-1], job7)
            dax.depends(jobs10[-1], jobs9[-1])

            file_aparc_aseg_mean_tract_lengths_csvs.append(File(TractsGenFiles.TRACT_LENGHTS.value % atlas_suffix))
            jobs11.append(Job(TractsGenJobNames.TCK2CONNECTOME.value,
                                  node_label="Generate tract lengths %s" % atlas_suffix))
            jobs11[-1].addArguments(file_strmlns_sift, file_vol_lbls[-1],
                                    "-assignment_radial_search", "2", "-scale_length",
                                    "-stat_edge", "mean", file_aparc_aseg_mean_tract_lengths_csvs[-1])
            jobs11[-1].uses(file_strmlns_sift, link=Link.INPUT)
            jobs11[-1].uses(file_vol_lbls[-1], link=Link.INPUT)
            jobs11[-1].uses(file_aparc_aseg_mean_tract_lengths_csvs[-1], link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(jobs11[-1])

            dax.depends(jobs11[-1], job7)
            dax.depends(jobs11[-1], jobs9[-1])

        return jobs10, jobs11
