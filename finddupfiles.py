__author__ = "Arjun Singh"
__email__ = "awesome.arjun11@gmail.com"

import argparse
import os
import xxhash   # import hashlib


def find_duplicates(args):
    """Driver function to find duplicate files
    """
    same_size = recursive_search_dupsize(args.path,recurse_flag=args.recursive)
    duplicates ={}
    for file_list in same_size.values():
        if len(file_list)>1:
            duplicates.update(same_hash_dict(file_list))

    action(duplicates,oflag=args.output,dflag=args.delete)


def recursive_search_dupsize(directory,recurse_flag =False, same_size = {}):
    """:param directory: Path of Directory to be searched
       :param recurse_flag: if True the subdirectories are searched too
       :param same_size: dictionary in format {FileSize:FilePath}
       :return: same_size dictionary
    """
    try:
        for entry in os.scandir(directory):
            if entry.is_dir():
                if recurse_flag:
                    same_size.update(recursive_search_dupsize(entry.path,recurse_flag=recurse_flag,same_size=same_size))
                else:
                    pass
            elif entry.is_file():
                size = os.stat(entry.path).st_size
                if size in same_size:
                    same_size[size].append(entry.path)
                else:
                    same_size[size] = [entry.path]
    except PermissionError as e:
        print(e)
    return same_size


def same_hash_dict(file_list):
    """:param file_list:
       :return: duplicates in format {FileHash:FilePath}
    """
    duplicates = {}
    for path in file_list:
        file_hash = hashfile(path)
        if file_hash in duplicates:
            duplicates[file_hash].append(path)
        else:
            duplicates[file_hash] = [path]
    return duplicates


def hashfile(path, blocksize=2**17):
    curr_file = open(path, 'rb')
    hasher = xxhash.xxh64()     #hasher = hashlib.md5()
    buf = curr_file.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = curr_file.read(blocksize)
    curr_file.close()
    return hasher.hexdigest()


def action(dup_dict, oflag=False, dflag=False):
    """:param dup_dict: Dictionary of all duplicate file
       :param oflag: if True writes output to a csv file
    """
    results = dup_dict.values()
    if len(results) > 0:
        print('Duplicates Found:')
        print("files with same content:")
        print('\n'+'___'*40)
        for result in results:
            for path in result:
                print('\t\t'+ path)
            print('___'*40)
    else:
        print('No duplicate files found.')
    if oflag:
        import csv
        with open('duplicatefiles.csv', 'w', newline='') as csvfile:
            dupwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            dupwriter.writerow(['FileName','FilePath'])
            for result in results:
                for path in result:
                    dupwriter.writerow([os.path.basename(path),path])
                dupwriter.writerow([])
    if dflag:
        for result in results:
            for path in result[1:]:
                os.remove(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to the directory to be scanned', type=str)
    parser.add_argument('-o','--output', help='get result in a CSV file',action='store_true')
    parser.add_argument('-r','--recursive', help='to search path recursively',action='store_true')
    parser.add_argument('-d', '--delete', help='deletes duplicate files ', action='store_true')
    args = parser.parse_args()
    find_duplicates(args)


if __name__ == '__main__':
    main()