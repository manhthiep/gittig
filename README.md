Gittig
=========

Tool for mirroring/syncing git mirrors and git repos.

Original ideas & Copyright: https://launchpad.net/linaro-android-gerrit-support

* Mirror directory structure:
<pre>
[mirror-root-dir]/[remote-url]/[project-path].git
</pre>
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

* Clone commands:

  * Clone working dirs/mirrors from manifest file:
      <pre>
      gittig clone [--mirror] --manifest=\<manifest-file\>
      </pre>
  * Clone working dirs/mirrors from URL:
      <pre>
      gittig clone [--mirror] --url=\<project-url\>
      </pre>
  * Clone from manifest file with project filters:
      <pre>
      gittig clone [--mirror] --manifest=\<manifest-file\> --project=\<project-local-path/project-name\>
      </pre>
  * Clone from manifest with remote (name/URL) filters
      <pre>
      gittig clone [--mirror] --manifest=\<manirest-file\> --remote=\<remote-name/remote-url\>
      </pre>
  * Clone from manifest with reference mirrors:
      <pre>
      gittig clone [--mirror] --manifest=\<manifest-file\> --reference=\<local-mirror-dir\>
      </pre>

* Sync commands:

  * Sync working dirs & mirrors from local directory (default is current directory):
      <pre>
      gittig sync [--local-dir=\<local-dir\>]
      </pre>
  * Sync working dirs & mirrors from local directory with project filters:
      <pre>
      gittig sync --project=\<project-local-path\> [--local-dir=\<local-dir\>]
      </pre>
  * Sync working dirs/mirrors from manifest file (map to local directory):
      <pre>
      gittig sync [--mirror] --manifest=\<manifest-file\>
      </pre>
  * Sync from manifest file with project filters:
      <pre>
      gittig sync [--mirror] --manifest=\<manifest-file\> --project=\<project-local-path/project-name\>
      </pre>
  * Sync from manifest with remote filters:
      <pre>
      gittig sync [--mirror] --manifest=\<manifest-file\> --remote=\<remote-name/remote-url\>
      </pre>
  * Sync from manifest with reference mirrors:
      <pre>
      gittig sync [--mirror] --manifest=\<manifest-file\> --reference=\<local-mirror-dir\>
      </pre>

* Options:
    <pre>
    --manifest=manifest-file
          Path to manifest file
    --url=project-url
          URL of git project
    --project=[project-local-path | project-name]
          Project filter string
    --remote=[remote-name | remote-url]
          Remote filter string
    --mirror
          Enable mirror cloning/syncing
    --local-dir=local-dir
          Working local directory (default is current directory)
    --config=config-file
          Path to config file (default is in current directory)
    --reference=local-mirror-dir
          Path to local mirror directory

    --ignore-project=project-local-path,project-name
          Project filter string, mutiple string allow (separated by comma)
    --ignore-remote=remote-name,remote-url
          Remote filter string, mutilple string allow (separated by comma)

    --dry-run
          Not actual run, only print verbose
    --debug
          Enable debug logging
    </pre>

* Config file: [**.gittig**]
  * Syntax
    <pre>
    [CONFIG]
    $var = val
    [remote-url]
    # this is a comment
    $var = val
    src-path = [local-path | skip]
    </pre>
  * See example .gittig in this directory

* Manifest file
  * Uses manifest file format of Google's repo tool
  * See examples in example-manifests directory  

Change logs
---------------
* 2014/07/14
    * Rename pygit.py to gittig ('tig' is 'git' in reverse, like mirroring).
* 2013/08/18:
    * Update pygit.py
    * Added script helpers for cloning & syncing
* 2012/09/24:
    * Removed git-repo.py & git-mirror.py
    * Tagged pygit.py - v1.1
* 2012/09/21:
    * Added pygit.py - combined funtions of git-mirror.py and git-repo.py
* 2012/09/15:
    * Initial commit
    * git-mirror.py - v1.0
    * git-repo.py - v1.0
    * Added example manifests
