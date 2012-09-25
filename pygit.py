#!/usr/bin/env python
# Original idea & copyright: https://launchpad.net/linaro-android-gerrit-support
# Combination of git-mirror.py & git-repo.py
# pygit.py - v1.2
#
# Use cases:
# =====================
# 1. Clone
# ------------
# 1.1. Clone working dirs/mirrors from manifest file:
#     pygit.py clone [--mirror] --manifest=<manifest-file>
# 1.2. Clone working dirs/mirrors from URL:
#     pygit.py clone [--mirror] --url=<project-url>
# 1.3. Clone from manifest file with project filters:
#     pygit.py clone [--mirror] --manifest=<manifest-file> --project=<project-local-path/project-name>
# 1.4. Clone from manifest with remote (name/URL) filters
#     pygit.py clone [--mirror] --manifest=<manirest-file> --remote=<remote-name/remote-url>
# 1.5. Clone from manifest with reference mirrors:
#     pygit.py clone [--mirror] --manifest=<manifest-file> --reference=<local-mirror-dir>
#
# 2. Sync
# ------------
# 2.1. Sync working dirs & mirrors from local directory (default is current directory):
#    pygit.py sync [--local-dir=<local-dir>]
# 2.2. Sync working dirs & mirrors from local directory with project filters:
#    pygit.py sync --project=<project-local-path> [--local-dir=<local-dir>]
# 2.3. Sync working dirs/mirrors from manifest file (map to local directory):
#    pygit.py sync [--mirror] --manifest=<manifest-file>
# 2.4. Sync from manifest file with project filters:
#    pygit.py sync [--mirror] --manifest=<manifest-file> --project=<project-local-path/project-name>
# 2.5. Sync from manifest with remote filters:
#    pygit.py sync [--mirror] --manifest=<manifest-file> --remote=<remote-name/remote-url>
# 2.6. Sync from manifest with reference mirrors:
#    pygit.py sync [--mirror] --manifest=<manifest-file> --reference=<local-mirror-dir>
#
# All arguments:
# =====================
#   --manifest=<manifest-file>
#         Path to manifest file
#   --url=<project-url>
#         URL of git project
#   --project=<project-local-path/project-name>
#         Project filter string, multiple string allow (separated by comma)
#   --remote=<remote-name/remote-url>
#         Remote filter string, multiple string allow (separated by comma)
#   --mirror
#         Enable mirror cloning/syncing
#   --local-dir=<local-dir>
#         Working local directory (default is current directory)
#   --config=<config-file>
#         Path to config file (default is in current directory)
#   --reference=<local-mirror-dir>
#         Path to local mirror directory
#   --ignore-project=<project-local-path/project-name>
#         Project filter string, mutiple string allow (separated by comma)
#   --ignore-remote=<remote-name/remote-url>
#         Remote filter string, mutilple string allow (separated by comma)
#
# Test and debug:
# =====================
#   --dry-run
#         Not actual run, only print verbose
#   --debug
#         Enable debug logging
#
import os
import sys
import time
import optparse
import logging
import urlparse
from xml.dom import minidom
import traceback
import subprocess
import re

# Definition
CONFIG_KEYWORD = "CONFIG"
CONFIG_FILE = ".pygit"

# Global variables
conf = None
ctrl = None
options = None
log = logging.getLogger(__file__)

optparser = optparse.OptionParser(usage="""%prog <options> <command> <args>...

Command:
  clone  - Clone any new projects from source (based on config & manifest)
  sync   - Sync remote updates (based on working copy or manifest)""")

optparser.add_option("-d", "--local-dir", metavar="DIR",
             dest="local_dir",
             help="Local root directory")
optparser.add_option("-c","--config", default=".pygit",
             dest="config",
             help="Config file to use (%default)")
optparser.add_option("-m","--manifest", metavar="NAME.xml",
             dest="manifest",
             help="Use manifest for list of projects")
optparser.add_option("-u","--url", metavar="URL",
             dest="url",
             help="URL to single git project")
optparser.add_option("-p", "--project", metavar="SUBSTR", default="",
             dest="project", 
             help="Project projects have name or local path matching filter string")
optparser.add_option("-r","--remote", metavar="SUBSTR", default="",
             dest="remote",
             help="Process remotes matching filter string")
optparser.add_option("--ignore-project", metavar="SUBSTR", default="",
             dest="ignore_project", 
             help="Do not process projects have name or local path matching filter string")
optparser.add_option("--ignore-remote", metavar="SUBSTR", default="",
             dest="ignore_remote",
             help="Do not process remotes matching filter string")
optparser.add_option("--reference", metavar="DIR", default="",
             dest="reference",
             help="Reference to mirror directory")
optparser.add_option("--mirror", action="store_true",
             help="Clone the mirror projects (only for 'clone' command)")
optparser.add_option("--dry-run", action="store_true",
             help="Don't make any changes")
optparser.add_option("-D","--debug", action="store_true",
             dest="debug",
             help="Enable debug logging")

def run_command(cmdline, favor_dry_run=True):
    err = 0
    if favor_dry_run and options.dry_run:
        log.info("Would run: %s", cmdline)
    else:
        log.debug("Running: %s", cmdline)
        err = os.system(cmdline)
    return err

class PyGitCommand(object):
           
    def __init__(self, project, cmd, gitdir=None, workdir=None):
        self.process = None
        git_cmd = ["git"]
        git_cmd.extend(cmd)
        if project:
            if workdir == None:
                workdir = project.worktree
            if gitdir == None:
                gitdir = project.gitdir
        if not workdir:
            workdir = os.getcwd()
        if gitdir:
            os.environ["GIT_DIR"] = gitdir
        if options.dry_run:
            cmdline = ' '.join(git_cmd)
            log.info("Would run: %s", cmdline)        
        else:
            cmdline = ' '.join(git_cmd)
            log.debug("In %s", workdir if workdir else os.getcwd())
            log.debug("Runing: %s", cmdline)
            try:
                p = subprocess.Popen(git_cmd, 
                                     cwd=workdir, 
                                     stdout=subprocess.PIPE)
            except Exception, e:
                log.error("Execute git command failed: %s", e)
                return
            self.process = p
        
    def wait(self):
        if options.dry_run:
            return 0
        if not self.process == None:
            try:
                p = self.process
                (self.stdout, self.stderr) = p.communicate()
            except Exception, e:
                log.error("Wait for git command failed: %s", e)
                return -1
            return p.returncode   
        return -1     
    
class PyGitProject(object):

    def __init__(self, name, path, remote, revision):
        self.name = name
        self.path = path
        self.remote = remote
        self.url = remote.fetch + "/" + name + ".git"
        self.is_checkout_tag = False
        if revision.startswith("refs/heads"):
            self.revision = revision[len("refs/heads")+1:]
        elif revision.startswith("refs/tags"):
            self.revision = revision[len("refs/tags")+1:]
            self.is_checkout_tag = True
        else:
            self.revision = revision
        self.is_bare_mirror = False
        self.worktree = None
        self.gitdir = None
        
    def _update_mirror(self):
        cmd = ["remote", "update"]
        err = PyGitCommand(self, cmd).wait()
        return err
    
    def _checkout_commit(self, commit, detach=False, quiet=True):
        cmd = ["checkout"]
        if quiet:
            cmd.append("--quiet")
        if detach:
            cmd.append("--detach")
        cmd.append(commit)
        err = PyGitCommand(self, cmd).wait()
        return err
    
    def _checkout_branch(self, branch, remote=None, 
                               remotebranch=None, track=False, quiet=True):
        cmd = ["checkout"]
        if quiet:
            cmd.append("--quiet")
        if track:
            cmd.append("--track")
        cmd.append(branch)
        if remote and remotebranch:
            cmd.append("%s/%s" % (remote, remotebranch))
        elif remotebranch:
            cmd.append("origin/%s" % remotebranch)
        elif remote:
            cmd.append("%s/%s" % (remote, branch))
        else:
            cmd.append("origin/%s" % branch)
        err = PyGitCommand(self, cmd).wait()
        return err
        
    def _fetch_all(self, fetchtags=True):
        cmd = ["fetch", "--all"]
        if fetchtags:
            cmd.append("--tags")
        err = PyGitCommand(self, cmd).wait()
        return err
    
    def _clone(self, mirror=False):
        cmd = ["clone"]
        if mirror:
            cmd.append("--mirror")
        cmd.append(self.url)
        if mirror:
            cmd.append(self.name + ".git")
        else:
            cmd.append(self.path)
        err = PyGitCommand(self, cmd, workdir=os.getcwd()).wait()
        return err     
    
    def clone(self, basedir):
        err = 0
        if self.is_bare_mirror:
            self.worktree = None
            self.gitdir = os.path.join(basedir, self.name + ".git")
        else:
            self.worktree = os.path.join(basedir, self.path)
            self.gitdir = self.worktree.rstrip("/") + "/.git"
            
        log.debug("self.worktree = %s", self.worktree)
        log.debug("self.gitdir = %s", self.gitdir)
            
        if os.path.exists(self.gitdir) and not os.listdir(self.gitdir) == []:
            log.debug("Target: '%s' already exists and is not empty, skipping", \
                      self.path if not self.is_bare_mirror else self.name + ".git")
            return 0
        
        os.chdir(basedir)
        log.debug("Enter %s", basedir)
        if not options.reference == "":
            git_url = os.path.join(options.reference.rstrip("/"), \
                                   self.remote.get_relpath() + "/" + self.name + ".git")
            if os.path.exists(git_url) and not os.listdir(git_url) == []:
                self.url = git_url
                
        log.info("Cloning %s", self.url)
        if self.is_bare_mirror:
            err = self._clone(mirror=True)
            if not err == 0:
                log.error("Error occurs (%d). Abort", err)
                return err
        else:
            err = self._clone()
            if not err == 0:
                log.error("Error occurs (%d). Abort", err)
                return err
            if not self.revision == "":                
                err = self._checkout_commit(self.revision)
                if not err == 0:
                    log.error("Error occurs (%d). Abort", err)
                    return err
        return 0
    
    def sync(self, basedir):
        err = 0
        os.chdir(basedir)
        log.debug("Enter %s", basedir)
        
        if self.is_bare_mirror:
            self.worktree = None
            self.gitdir = os.path.abspath(self.name + ".git")
        else:
            self.workdir = os.path.abspath(self.path)
            self.gitdir = self.workdir.rstrip("/") + "/.git"
            
        if os.path.exists(self.gitdir) and not os.listdir(self.gitdir) == []:
            # Fetch the project                   
            log.debug("Fetching %s", self.url)
            if self.is_bare_mirror:
                err = self._update_mirror()
            else:
                err = self._fetch_all()
            if not err == 0:
                log.error("Error occurs (%d). Abort", err)
                return err
            if not self.revision == "" and not self.is_bare_mirror:
                             
                refs_heads_path = os.path.join(self.gitdir, "/refs/heads/%s" % self.revision)
                refs_tags_path = os.path.join(self.gitdir, "/refs/tags/%s" % self.revision)
                
                if os.path.exists(refs_heads_path) or os.path.exists(refs_tags_path):
                    err = self._checkout_commit(self.revision)
                else:
                    err = self._checkout_commit(self.revision)
                if not err == 0:
                    log.error("Error occurs (%d). Abort", err)
                    return err
        elif os.path.exists(self.gitdir):
            log.error("Target: '%s' is empty, skipping", self.gitdir)
            return 0
        else:
            # Clone the project
            if not options.reference == "":
                git_url = os.path.join(options.reference, \
                                       self.remote.get_relpath() + "/" + self.name + ".git")
                if os.path.exists(git_url) and not os.listdir(git_url) == []:
                    # Update project fetch URL
                    self.url = git_url
                    
            log.debug("Cloning %s", self.url)
            if self.is_bare_mirror:
                err = self._clone(mirror=True)
                if not err == 0:
                    log.error("Error occurs (%d). Abort", err)
                    return err
            else:
                err = self._clone()
                if not err == 0:
                    log.error("Error occurs (%d). Abort", err)
                    return err
                if not self.revision == "":    
                    err = self._checkout_commit(self.revision)
                    if not err == 0:
                        log.error("Error occurs (%d). Abort", err)
                        return err
        return err
    
class PyGitRemote(object):
    
    def __init__(self, name, fetch, in_config=False):
        self.name = name.rstrip("/")
        self.fetch = fetch
        self.projects = []
        self.vars = {}
        self.rules = {}
        self.is_in_config = in_config
        
    def get_relpath(self):
        remote_p = urlparse.urlparse(self.fetch)
        remote_relpath = remote_p.netloc.rstrip("/") + remote_p.path
        return remote_relpath

    def add_project(self, project):
        for p in self.projects:
            if project.name == p.name:
                log.info("Project '%s' already in remote '%s'. Skip", project.name, self.name)
                return 0
        self.projects.append(project)
        return 1

    def get_projects(self):
        return self.projects

    def store_var(self, var, val):
        self.vars[var] = val

    def get_var(self, var):
        return self.vars.get(var)

    def get_bool(self, val):
        val2 = val.lower()
        if val2 in ("true", "on", "1"):
            return True
        if val2 in ("false", "off", "0"):
            return False
        assert False, "Syntax error: boolean value expected, got: " + val

    def store_rule(self, field1, field2):
        if self.get_bool(self.vars.get("active", "true")):
            self.rules[field1] = field2

    def get_rules(self):
        return self.rules

class PyGitConfig(object):

    def __init__(self, local_dir):
        self.configs = {}
        self.remotes = []
        self.local_dir = local_dir

    def parse(self, config_file):
        in_file = open(config_file)
        git_remote = None
        config_section = 0
        for line in in_file:
            line = line.strip()
            if not line:
                continue
            if line[0] == "#":
                continue
            if line[0] == "[":
                # Declare new remote
                remote_url = line[1:-1]
                if not remote_url.startswith(CONFIG_KEYWORD):
                    assert "://" in remote_url, "URL schema is required in " + line
                    git_remote = PyGitRemote("from_config", remote_url, True)       
                    self.remotes.append(git_remote)
                    config_section = 0
                else:
                    config_section = 1
            else:
                fields = line.split("=", 1)
                fields = [f.strip() for f in fields]
                if fields[0][0] == "$":
                    # Variable spec
                    # $<var-name> = <value>
                    if config_section == 0:
                        if not git_remote == None:
                            git_remote.store_var(fields[0][1:], fields[1])
                        else:
                            assert False, "Syntax error: Variable is defined not within remote."
                    else:
                        self.configs[fields[0][1:]] = fields[1]
                else:
                    # Repository rule spec
                    # <project-name> = <dest-path> or 'skip'
                    if not config_section == 0:
                        assert False, "Syntax error: Rules are defined only within remote."
                    else:
                        if len(fields) == 1:
                            fields.append(fields[0])
                        if not git_remote == None:
                            git_remote.store_rule(fields[0], fields[1])
                        else:
                            assert False, "Syntax error: Rule is defined not within remote."
        # Done, close file
        in_file.close()

    def store(self, config_file):
        in_file = open(config_file)
        in_file.close()

    def get_local_dir(self):
        return self.local_dir.rstrip("/") + "/"

    def add_remote(self, remote):
        for r in self.remotes:
            if r.fetch == remote.fetch or r.name == remote.name:
                log.debug("Remote '%s' (%s) already defined. Skip.", remote.fetch, remote.name)
                # Update the name if remote (which read from config) has same fetch URL
                if r.name == "from_config":
                    r.name = remote.name
                return -1
        log.debug("Adding remote '%s'(%s)", remote.fetch, remote.name)
        self.remotes.append(remote)
        return 0

    def find_remote(self, name):
        for r in self.remotes:
            if r.name == name:
                return r
        return None

    def get_remotes(self, r_match=[], r_notmatch=[]):
        remotes = []
        for r in self.remotes:
            if len(r_notmatch) > 0:
                ignore = False
                for str in r_notmatch:
                    if str in r.fetch or str == r.name:
                        ignore = True
                        break
                if ignore:
                    log.info("remote '%s' is forcibly ignored", r.fetch)
                else:
                    remotes.append(r)
            elif len(r_match) > 0:
                for str in r_match:
                    if str in r.fetch or str == r.name or r.name == "local_dir":
                        remotes.append(r)
                        break
            else:
                remotes.append(r)
        return sorted(remotes, key=lambda remote: remote.fetch)

    def add_project_to_remote(self, git_remote, git_project):
        return git_remote.add_project(git_project)
        
class PyGitControl(object):
        
    def scan_dir_for_projects(self, basedir):
        log.info("Scanning repos in '%s'...", basedir)
        for root, dirs, files in os.walk(basedir):
            if root.endswith(".git"):
                dirs[:]=[]
                continue
            dirs.sort()
            if ".git" in dirs:
                # root is a working repository
                # Project's name and project's path as relative path
                p_name = root[len(basedir):]
                # Dummy remote (TODO: get from working directory)
                # Now, all projects are belong to 'local_dir' remote
                # Later command on this remote doesn't use remote.fetch
                dummy_remote = conf.find_remote("local_dir")
                if dummy_remote == None:
                    dummy_remote = PyGitRemote("local_dir", "")
                    conf.add_remote(dummy_remote)                    
                # Create a new project
                log.debug("[1] remote=%s, p_name=%s", dummy_remote.name, p_name)
                git_project = PyGitProject(p_name, p_name, dummy_remote, "")
                # Add the project to remote
                conf.add_project_to_remote(dummy_remote, git_project)
                # Do not enter deeper
                dirs[:] = []
            else:    
                for d in dirs:            
                    if d.endswith(".git"):
                        # d is a mirror
                        abspath = os.path.join(root, d)
                        # Project's name and project's path as relative path                    
                        p_name = abspath[len(basedir):-len(".git")]
                        # Dummy remote (TODO: get from working directory)
                        # Now, all projects are belong to 'local_dir' remote
                        # Later command on this remote doesn't use remote.fetch
                        dummy_remote = conf.find_remote("local_dir")
                        if dummy_remote == None:
                            dummy_remote = PyGitRemote("local_dir", "")
                            conf.add_remote(dummy_remote)                    
                        # Create a new project
                        log.debug("[2] remote=%s, p_name=%s", dummy_remote.name, p_name)
                        git_project = PyGitProject(p_name, p_name, dummy_remote, "")
                        git_project.is_bare_mirror = True
                        # Add the project to remote
                        conf.add_project_to_remote(dummy_remote, git_project)

    def parse_manifest_for_projects(self, manifest, is_mirror=False):
        log.info("Parsing manifest file '%s'", os.path.abspath(manifest))
        dom = minidom.parse(manifest)
        # Get remote list
        for r in dom.getElementsByTagName("remote"):
            r_name = r.getAttribute("name")
            r_fetch_url = r.getAttribute("fetch").rstrip("/")
            git_remote = PyGitRemote(r_name, r_fetch_url)
            conf.add_remote(git_remote)
        # Get default remote
        default_remote_alias = ""
        default_revision = ""
        default_conf = dom.getElementsByTagName("default")
        if len(default_conf) >= 1:
            if len(default_conf) > 1:
                log.warning("Multiple default remote in manifest. Take only fist item")
            default_remote_alias = default_conf[0].getAttribute("remote")
            default_revision = default_conf[0].getAttribute("revision")
        # Get all projects
        for p in dom.getElementsByTagName("project"):
            p_name = p.getAttribute("name")
            p_path = p.getAttribute("path")
            p_remote_alias = p.getAttribute("remote")
            p_revision = p.getAttribute("revision")
            if p_revision == "" and not default_revision == "":
                p_revision = default_revision        
            # Assign to default remote if the project does not specify
            if p_remote_alias == "":
                if default_remote_alias == "":
                    log.warning("This project is not belong any remote :(")
                else:
                    p_remote_alias = default_remote_alias
            # Find the remote object
            git_remote = conf.find_remote(p_remote_alias)
            if not git_remote == None:
                log.debug("Add project '%s' for remote '%s'.", p_name, p_remote_alias)
                if p_path == "":     
                    git_project = PyGitProject(p_name, p_name, git_remote, p_revision)
                else:
                    git_project = PyGitProject(p_name, p_path, git_remote, p_revision)
                if is_mirror:
                    git_project.is_bare_mirror = True
                conf.add_project_to_remote(git_remote, git_project)
            else:
                log.warning("Skip project '%s' for remote '%s'.", p_name, p_remote_alias)        

    def get_projects_for_a_remote(self, remote, p_match=[], p_notmatch=[]):
        """Get projects for a remote (rules applied)"""
        projects = remote.get_projects()
        rules = remote.get_rules()
        projects_d = []
        log.debug("Remote %s ('%s'):", remote.name, remote.fetch)
        for p in projects:
            if rules.has_key(p.name):
                val = rules.get(p.name)
                if  val == "skip":
                    log.info("Skip downloading '%s' (forced by config)", p.url)
                else:       
                    # Update project path following rule         
                    p.path = val
                    if len(p_notmatch) > 0:
                        ignore = False
                        for str in p_notmatch:
                            if str in p.path or str in p.name:
                                ignore = True
                                break
                        if ignore:
                            log.info("Project '%s' is forcibly ignored", p.name)
                        else:
                            log.debug("Download '%s' --> '%s' (forced by config)", p.name, val)
                            projects_d.append(p)
                    elif len(p_match) > 0:
                        for str in p_match:
                            if str in p.path or str in p.name:
                                log.debug("Download '%s' --> '%s' (forced by config)", p.name, val)
                                projects_d.append(p)
                                break
                    else:
                        log.debug("Download '%s' --> '%s' (forced by config)", p.name, val)
                        projects_d.append(p)
            elif len(p_notmatch) > 0:
                ignore = False 
                for str in p_notmatch:
                    if str in p.path or str in p.name:
                       ignore = True 
                       break
                if ignore:
                    log.info("Project '%s' is forcibly ignored", p.name)
                else:
                    log.debug("Download '%s' --> '%s'", p.name, p.name if options.mirror else p.path)
                    projects_d.append(p)
            elif len(p_match) > 0:
                for str in p_match:
                    if str in p.path or str in p.name:
                        log.debug("Download '%s' --> '%s'", p.name, p.name if options.mirror else p.path)
                        projects_d.append(p)
                        break
            else:
                log.debug("Download '%s' --> '%s'", p.name, p.name if options.mirror else p.path)
                projects_d.append(p)  
        return sorted(projects_d, key=lambda project: project.path)

    def get_all_projects(self, r_match=[], r_notmatch=[],
                         p_match=[], p_notmatch=[]):
        """Get projects which have path or name matches with p_match[] and not match p_notmatch[]"""
        projects_f = []
        # Scan all remotes
        for remote in conf.get_remotes(r_match, r_notmatch):
            projects = self.get_projects_for_a_remote(remote, p_match, p_notmatch)
            for p in projects:
                projects_f.append(p)
        return projects_f

    def clone_projects(self, basedir, projects):
        """Clone projects from remote server"""
        count = 0
        total = len(projects)
        if total == 0:
            log.warning("Nothing to clone.")
        else:
            if not os.path.exists(basedir):
                try:
                    os.makedirs(basedir)
                except OSError:
                    pass
            os.chdir(basedir)
            log.info("Enter %s", basedir)
            for p in projects:
                count = count + 1
                log.info("Cloning projects: '%s' (%d/%d)", p.name, count, total)
                err = p.clone(basedir)
                if not err == 0:
                    sys.exit(err)

    def sync_projects(self, basedir, projects):
        """Update projects from remote server"""
        count = 0
        err = 0
        total = len(projects)
        if total == 0:
            log.warning("Nothing to sync.")
        else:
            if not os.path.exists(basedir):
               try:
                   os.makedirs(basedir)
               except OSError:
                   pass 
            log.info("Enter %s", basedir)
            for p in projects:
                count = count + 1
                log.info("Syncing projects: '%s' (%d/%d)", p.path, count, total)
                err = p.sync(basedir)
                if not err == 0:
                    sys.exit(err)
                    
def do_clone(control):
    if options.manifest:
        control.parse_manifest_for_projects(options.manifest, options.mirror)
        for remote in conf.get_remotes(options.remote, options.ignore_remote):
            projects = control.get_projects_for_a_remote(remote, options.project, options.ignore_project)
            if len(projects) > 0:
                if options.mirror:
                    basedir = os.path.join(conf.get_local_dir(), remote.get_relpath())
                else:
                    basedir = conf.get_local_dir()
                log.info("=== Processing: %s (%d Repositories) ===", remote.fetch, len(projects))
                control.clone_projects(basedir, projects)
    elif options.url:
        projects = []
        
        s = options.url.rfind("/")
        p_path = options.url[s+1:-len(".git")]
        remote_url = options.url[:s]
        dummy_remote = PyGitRemote("url", remote_url)
        
        git_project = PyGitProject(p_path, p_path, dummy_remote, "")
        if options.mirror:
            git_project.is_bare_mirror = True
        projects.append(git_project)
        
        log.info("=== Processing: %s (%d Repositories) ===", dummy_remote.fetch, len(projects))
        control.clone_projects(conf.get_local_dir(), projects)
    else:
        optparser.error("Please provide git project(s) by --manifest or --url")
        
def do_sync(control):
    if options.manifest:
        control.parse_manifest_for_projects(options.manifest, options.mirror)            
        for remote in conf.get_remotes(options.remote, options.ignore_remote):
            projects = control.get_projects_for_a_remote(remote, options.project, options.ignore_project)
            if len(projects) > 0:
                if options.mirror:
                    basedir = os.path.join(conf.get_local_dir(), remote.get_relpath())
                else:
                    basedir = conf.get_local_dir()
                log.info("=== Processing: %s (%d Repositories) ===", remote.fetch, len(projects))
                control.sync_projects(basedir, projects)
    else:
        control.scan_dir_for_projects(conf.get_local_dir())
        projects = control.get_all_projects(options.remote, options.ignore_remote, options.project, options.ignore_project)
        if len(projects) > 0:
            log.info("=== Processing: %d Repositories ===", len(projects))
            control.sync_projects(conf.get_local_dir(), projects)
            
def do_sub_command(sub_command):
    ctrl = PyGitControl()
    if sub_command == "clone":
        do_clone(ctrl)
    elif sub_command == "sync":
        do_sync(ctrl)
    else:
        optparser.error("Unknown command")
        
def main():
    global conf
    global options

    options, args = optparser.parse_args(sys.argv[1:])
    if len(args) < 1:
        optparser.error("Wrong number of arguments")

    logging.basicConfig(format='%(levelname)s: %(message)s', \
                        level=logging.DEBUG if options.debug else logging.INFO)

    if options.remote != "":
        options.remote = re.split(',|;', options.remote)
        log.debug("options.remote=%s", options.remote)
    if options.ignore_remote != "":
        options.ignore_remote = re.split(',|;', options.ignore_remote)
        log.debug("options.ignore_remote=%s", options.ignore_remote)
    if options.project != "":
        options.project = re.split(',|;', options.project)
        log.debug("options.project=%s", options.project)
    if options.ignore_project != "":
        options.ignore_project = re.split(',|;', options.ignore_project)
        log.debug("options.ignore_project=%s", options.ignore_project)

    # Mirror directory settings
    if options.local_dir:
        # Provided path
        local_dir = os.path.abspath(options.local_dir)
    else:
        # Current directory
        local_dir = os.getcwd()

    if not os.path.isdir(local_dir):
        optparser.error("Local dir is not exist in provided path (--local-dir or -d)")
          
    conf = PyGitConfig(local_dir)
    # Read configs from file
    if options.config:
        if os.path.isfile(options.config):
            # Config file in provided path
            log.info("Reading config file '%s'", os.path.abspath(options.config))
            conf.parse(options.config)
        else:
            optparser.error("Config file is not exist in provided path (--config)")
    elif os.path.isfile(conf.get_local_dir() + CONFIG_FILE):
        # Config file under mirror dir
        log.info("Reading config file '%s'", conf.get_local_dir() + "/" + CONFIG_FILE)
        conf.parse(conf.get_local_dir() + CONFIG_FILE)
    elif os.path.isfile(os.path.abspath(CONFIG_FILE)):
        # Config file under current directory
        log.info("Reading config file '%s'", os.path.abspath(CONFIG_FILE))
        conf.parse(os.path.abspath(CONFIG_FILE))
        
    try:
        do_sub_command(args[0])
        log.info("Done.")
    except KeyboardInterrupt:
        log.error("Interrupted by keyboard...exiting")
    except Exception:
        traceback.print_exc(file=sys.stdout)    
    sys.exit(0)

if __name__ == "__main__":
    main()
