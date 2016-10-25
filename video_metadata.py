import os, sys, subprocess, json

#from video_metadata import get_multimedia_metadata, find_executable
def get_metadata(file):

    video_metadata = get_multimedia_metadata("test_video.mov", find_executable("ffprobe"))
    
    vertical_pixels = video_metadata['streams'][1]['height']
    if vertical_pixels > 2159:
        quality = "UHD"
    elif vertical_pixels > 1079:
        quality = "FHD"
    else:
        quality = "HD"

    duration = int(video_metadata['streams'][1]['duration'])

    return quality, duration
#

def is_executable(fname_abs):
    """
    Checks if the given file name is a regular file and if it is an
    executable by the current user.
    """
    result = False
    if os.path.isfile(fname_abs) and os.access(fname_abs, os.X_OK):
        result = True
    return result

def escape_file_name(fname):
    """
    Helper function to safely convert the file name (a.k.a. escaping) with
    spaces which can cause issues when passing over to the command line.
    """
    result = fname.replace('\"', '\\"') # escapes double quotes first
    result = ['"',result,'"']
    return "".join(result)


def find_executable(executable, path=None):
    # cross-platofrm way to find executable
    # inspired by http://snippets.dzone.com/posts/show/6313
    # and
    # http://stackoverflow.com/questions/377017/
    """
    Attempts to find executable file in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).
    Returns the complete filename or None if no such file is found.
    """

    if path is None:
        path = os.environ['PATH']

    paths = path.split(os.pathsep)
    extlist = ['']
    if sys.platform == 'win32':
        # checks if the provided executable file name has an extension
        # and if not - then search for all possible extensions
        # in order as defined by the 'PATHEXT' environmental variable
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext

    result = None
    for ext in extlist:
        execname = executable + ext
        abs_execname = os.path.abspath(execname)
        # checks if the file exists, is a normal file and can be executed
        if is_executable(abs_execname):
            result = abs_execname
            break
        else:
            for p in paths:
                f = os.path.join(p, execname)
                abs_f = os.path.abspath(f)
                if is_executable(abs_f):
                    result = abs_f
                    break

    return result

def get_multimedia_metadata(file_path, ffprobe_path):
    """
    Get the infomation about multimedia (audio, video or even some
    image formats) from :program:`ffprobe` command (part of 
    `ffmpeg <http://ffmpeg.org/>`_).
    
    Requires providing the path to the *ffprobe* external binary with
    permissions to execute it. It then parses the output and converts it to
    Python dictionary. Raises :exc:`ExtractorException` if it cannot find
    the :program:`ffprobe` binary or the output is not as expected.
    """
    if ffprobe_path: 
        if not os.path.isfile(ffprobe_path):
            errmsg = "Cannot find 'ffprobe' at: " + str(ffprobe_path)
            raise GeneralException(errmsg)

    # work around the issue with invoking the executable under Windows/Linux
    # Linux - shell must be True otherwise Popen can't find the file
    # Windows - shell must be False to avoid unnecessary invoking the command
    # shell
    use_shell = True
    if sys.platform.startswith('win'):
        use_shell = False

    escaped_fpath = escape_file_name(file_path)
    ffprobe_pipe = subprocess.Popen(
        " ".join([ffprobe_path,
                  '-print_format json',
                  '-show_format',
                  '-show_streams',
                  escaped_fpath]),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=use_shell
    )
    
    ffprobe_output = ffprobe_pipe.stdout.readlines()
    ffprobe_err = ffprobe_pipe.stderr.readlines()
    
    if ffprobe_output == []:
        err_msg = "".join(ffprobe_err)
        raise GeneralException("Error while invoking ffprobe:\n" + err_msg)
        
    ffprobe_json = []
    skip_line = True
    # cleanse any additional information that is not valid JSON
    for line in ffprobe_output:
        if line.strip() == '{':
            skip_line = False
        if not skip_line:
            ffprobe_json.append(line)
            
    result = json.loads("".join(ffprobe_json))
    return result

