import os
import subprocess
import multiprocessing

import click

from dlo_hic.utils.wrap.bwa import BWA
from dlo_hic.utils import read_args


def beds2bedpe(bed1, bed2, bedpe_filename):
    # build bed's index
    cmd = "join -j 4 {} {}".format(bed1, bed2)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    with open(bedpe_filename, 'w') as f:
        for line in p.stdout:
            items = line.strip().split()
            name, chr_a, s_a, e_a, score_a, strand_a,\
                  chr_b, s_b, e_b, score_b, strand_b = items
            outitems = [chr_a, s_a, e_a,
                        chr_b, s_a, e_a,
                        name, "1", strand_a, strand_b]
            outline = "\t".join(outitems) + "\n"
            f.write(outline)


@click.command(name="build_bedpe")
@click.option("--file-format", "-f",
    default="fastq",
    type=click.Choice(['fastq', 'bam', 'sam']))
@click.argument("input1", nargs=1)
@click.argument("input2", nargs=1)
@click.argument("bedpe", nargs=1)
@click.option("--ncpu", "-p",
    type=int,
    default=multiprocessing.cpu_count(),
    help="how many threads used to run bwa")
@click.option("--bwa-index", required=True, help="The bwa index prefix.")
@click.option("--mapq",
    default=20,
    help="the mapq threshold used to filter mapped records. default 20")
def _main(file_format, input1, input2, bedpe, ncpu, bwa_index, mapq):
    """ Build bedpe file from fastq or sam/bam file. """
    pre_1 = os.path.splitext(input1)[0] # prefix
    pre_2 = os.path.splitext(input2)[0]
    if file_format == 'fastq':
        # alignment firstly if the input format is fastq
        assert bwa_index is not None
        bwa = BWA(bwa_index)
        bwa.run(input1, pre_1, thread=ncpu, mem=False)
        bwa.run(input2, pre_2, thread=ncpu, mem=False)
        bam1 = pre_1 + '.bam'
        bam2 = pre_2 + '.bam'
    else:
        bam1 = input1
        bam2 = input2
    subprocess.check_call("samtools view {} -b -q {} > {}.filtered.bam".format(bam1, mapq, pre_1), shell=True)
    subprocess.check_call("samtools view {} -b -q {} > {}.filtered.bam".format(bam2, mapq, pre_2), shell=True)
    bed1 = pre_1 + ".bed"
    bed2 = pre_2 + ".bed"
    subprocess.check_call("bedtools bamtobed -i {} | sort -k4,4 > {}".format(pre_1+'.filtered.bam', bed1), shell=True)
    subprocess.check_call("bedtools bamtobed -i {} | sort -k4,4 > {}".format(pre_2+'.filtered.bam', bed2), shell=True)
    beds2bedpe(bed1, bed2, bedpe)


main = _main.callback


if __name__ == "__main__":
    _main()