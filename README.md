pygit.py
=========

Original ideas & Copyright: https://launchpad.net/linaro-android-gerrit-support
For cloning/fetching local git mirrors

* Mirror directory structure:
<pre>
[mirror-root-dir]/[remote-url]/[project-path]\<.git\>
</pre>
* Example:
<pre>
[mirror-root-dir]
 |---- android.git.linaro.org
 |     |---- device
 |     |     |---- common.git
 |     |     |---- ...
 |     |---- platform
 |---- android.googlesource.com
 |---- github.com
       |---- manhthiep/
       |---- CyanogenMod/
       |---- Evervolv/
</pre>
* Working directory structure:
<pre>
[working-root-dir]/[project-path]
</pre>
* Example:
<pre>
[android]
 |---- abi
 |     |---- cpp
 |           |---- .git
 |---- bionic
 |---- bootable                    
 |---- build
 |---- cts
 |---- dalvik
 |---- development
 |---- device
 |         |---- common
 |         |---- generic
 |         |---- ...
 |---- external
 |---- ...
</pre>
1. Clone commands:
  * 1.1. Clone working dirs/mirrors from manifest file:
      <pre>
      pygit clone [--mirror] --manifest=<manifest-file>
      </pre>
  * 1.2. Clone working dirs/mirrors from URL:
      <pre>
      pygit clone [--mirror] --url=<project-url>
      </pre>
  * 1.3. Clone from manifest file with project filters:
      <pre>
      pygit clone [--mirror] --manifest=<manifest-file> --project=<project-local-path/project-name>
      </pre>
  * 1.4. Clone from manifest with remote (name/URL) filters
      <pre>
      pygit clone [--mirror] --manifest=<manirest-file> --remote=<remote-name/remote-url>
      </pre>
  * 1.5. Clone from manifest with reference mirrors:
      <pre>
      pygit clone [--mirror] --manifest=<manifest-file> --reference=<local-mirror-dir>
      </pre>

2. Sync commands:

  * 2.1. Sync working dirs & mirrors from local directory (default is current directory):
      <pre>
      pygit sync [--local-dir=<local-dir>]
      </pre>
  * 2.2. Sync working dirs & mirrors from local directory with project filters:
      <pre>
      pygit sync --project=<project-local-path> [--local-dir=<local-dir>]
      </pre>
  * 2.3. Sync working dirs/mirrors from manifest file (map to local directory):
      <pre>
      pygit sync [--mirror] --manifest=<manifest-file>
      </pre>
  * 2.4. Sync from manifest file with project filters:
      <pre>
      pygit sync [--mirror] --manifest=<manifest-file> --project=<project-local-path/project-name>
      </pre>
  * 2.5. Sync from manifest with remote filters:
      <pre>
      pygit sync [--mirror] --manifest=<manifest-file> --remote=<remote-name/remote-url>
      </pre>
  * 2.6. Sync from manifest with reference mirrors:
      <pre>
      pygit sync [--mirror] --manifest=<manifest-file> --reference=<local-mirror-dir>
      </pre>

3. Options:
    <pre>
    --manifest=<manifest-file>
          Path to manifest file
    --url=<project-url>
          URL of git project
    --project=<project-local-path/project-name>
          Project filter string
    --remote=<remote-name/remote-url>
          Remote filter string
    --mirror
          Enable mirror cloning/syncing
    --local-dir=<local-dir>
          Working local directory (default is current directory)
    --config=<config-file>
          Path to config file (default is in current directory)
    --reference=<local-mirror-dir>
          Path to local mirror directory
    --dry-run
          Not actual run, only print verbose
    --debug
          Enable debug logging
    </pre>

4. Config file: [**.pygit**]
  * Syntax
    <pre>
    [CONFIG]
    $var = val
    
    [remote-url]
    #comment
    $var = val
    \<src-path\> = \<local-path\> <--- mapping rule
    </pre>

Change logs
---------------
* 2012/09/15: 
    * Initial commit
    * git-mirror.py - v1.0
    * git-repo.py - v1.0
    * Added example manifests
* 2012/09/21:
    * Added pygit.py - combined funtions of git-mirror.py and git-repo.py
* 2012/09/24:
    * Removed git-repo.py & git-mirror.py
    * Tagged pygit.py - v1.1

