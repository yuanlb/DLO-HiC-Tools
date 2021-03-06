"""

stream processing functions,
using the `yield` syntax.

"""

import logging

log = logging.getLogger(__name__)


def read_file(path):
    """
    Read a text file, yield lines.
    Support gziped file.
    """
    from .filetools import open_file
    with open_file(path) as f:
        for line in f:
            line = line.strip()
            yield line


def beds2bedpe(bed1_path, bed2_path):
    """
    merge two ends bed file to bedpe.
    """
    import subprocess as subp
    cmd = "join -j 4 {} {}".format(bed1_path, bed2_path)
    p = subp.Popen(cmd, shell=True, stdout=subp.PIPE)
    #
    # format joined bed bedpe
    for line in p.stdout:
        line = line.decode("utf-8")
        items = line.strip().split()
        name, chr_a, s_a, e_a, score_a, strand_a, \
        chr_b, s_b, e_b, score_b, strand_b = items
        outitems = [chr_a, s_a, e_a,
                    chr_b, s_b, e_b,
                    name, '0', strand_a, strand_b]
        outline = "\t".join(outitems)
        yield outline


def upper_triangle(line_iterator, fmt='bedpe'):
    """
    transform bedpe file's all line to upper trangle form.

    Arguments
    ---------
    fmt : str
        The input line format, 'bedpe' or 'pairs'
    """
    from dlo_hic.utils.parse_text import Bedpe, Pairs
    itr = line_iterator
    for line in itr:
        if fmt == 'bedpe':
            o = Bedpe(line)
            o.to_upper_trangle()
        elif fmt == 'pairs':
            o = Pairs(line)
            o.to_upper_trangle()
        else:
            raise ValueError("fmt only 'bedpe' or 'pairs'.")
        outline = str(o)
        yield outline


def remove_redundancy(line_iterator, fmt, distance):
    """
    Remove redundancy lines in the interaction(BEDPE/Pairs) file,
    input file must in upper triangular form and sorted according to reads1(chr and position).

    If pairs both ends's distance,
    small than the threshold distance at same time,
    consider them as the redundancy.

    for example:
        reads1    <---  ...  --->
               |-----|      |-----|
        reads2   <--- ... --->

        reads2 can be consider as the replication of reads1.
        reads2 will be remove.

    Arguments
    ---------
    fmt : str
        The input line format, 'bedpe' or 'pairs'
    distance : int
        Threshold distance, if distance less than this treat as the redundancy reads.
    """
    from dlo_hic.utils.parse_text import Bedpe, Pairs
    itr = line_iterator

    if fmt == "bedpe":
        fmt = Bedpe
    elif fmt == "pairs":
        fmt = Pairs
    else:
        raise ValueError("fmt only 'bedpe' or 'pairs'.")

    base = fmt(next(itr))
    while True:
        for line in itr:
            another = fmt(line)
            if base.is_rep_with(another, distance):  # is replication, check next line.
                continue
            else:  # not replication, output base line and change base line.
                out_line = str(base)
                yield out_line
                base = another
                break
        else:  # arrive at end of file.
            out_line = str(base)
            yield out_line
            break


def bedpe2pairs(line_iterator, pos1='start', pos2='start'):
    """
    Convert the line format from BEDPE to Pairs.
    """
    from dlo_hic.utils.parse_text import Bedpe
    itr = line_iterator
    for line in itr:
        bpe = Bedpe(line)
        pairs_line = bpe.to_pairs_line(pos1, pos2)
        yield pairs_line


def sort_pairs(pairs_path, ncpu=8):
    """ sort pairs file. """
    import subprocess as subp
    cmd = "sort --parallel={} -k2,2 -k4,4 -k3,3n -k5,5n {}".format(ncpu, pairs_path)
    p = subp.Popen(cmd, shell=True, stdout=subp.PIPE)
    for line in p.stdout:
        line = line.decode('utf-8')
        outline = line.strip()
        yield outline


def sort_bedpe(bedpe_path, ncpu=8):
    """ sort bedpe file. """
    import subprocess as subp
    cmd = "sort --parallel={} -k1,1 -k4,4 -k2,2n -k5,5n -k4,4n -k6,6n {}".format(ncpu, bedpe_path)
    p = subp.Popen(cmd, shell=True, stdout=subp.PIPE)
    for line in p.stdout:
        line = line.decode('utf-8')
        outline = line.strip()
        yield outline


def sort_bedpe_reads1(bedpe_path, ncpu=8):
    """ sort BEDPE file according to first 3 col(reads1). """
    import subprocess as subp
    cmd = "sort --parallel={} -k1,1V -k2,2n -k3,3n {}".format(ncpu, bedpe_path)
    p = subp.Popen(cmd, shell=True, stdout=subp.PIPE)
    for line in p.stdout:
        line = line.decode('utf-8')
        outline = line.strip()
        yield outline


def write_to_file(line_iterator, output_path, mode='w'):
    """
    Write lines in the iterator to a file,
    add a '\n' to the end.
    """
    itr = line_iterator
    with open(output_path, mode) as of:
        for line in itr:
            of.write(line + "\n")
