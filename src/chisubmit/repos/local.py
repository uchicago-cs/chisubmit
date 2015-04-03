import git
from git.exc import GitCommandError
from chisubmit.common import ChisubmitException
from gitdb.exc import BadObject
from chisubmit.repos import GitCommit, GitTag
import datetime

class LocalGitRepo(object):
    def __init__(self, directory):
        self.repo = git.Repo(directory)

        self.remotes = dict([(r.name, r) for r in self.repo.remotes])

    @classmethod
    def create_repo(cls, directory, bare = False, clone_from_url = None, remotes = []):
        if clone_from_url is None:
            git.Repo.init(directory, bare = bare)
        else:
            repo = git.Repo.clone_from(clone_from_url, directory)

            for remote_name, remote_url in remotes:
                repo.create_remote(remote_name, remote_url)

            return cls(directory)

    def fetch(self, remote_name, branch = None):
        if branch is None:
            self.remotes[remote_name].fetch()
        else:
            self.remotes[remote_name].fetch("%s:%s" % (branch, branch))

    def reset_branch(self, remote_name, branch):
        branch_refpath = "refs/heads/%s" % branch
        remote_branch_refpath = "refs/remotes/%s/%s" % (remote_name, branch)

        branch_head = self.__get_head(branch_refpath)
        remote_branch = self.__get_ref(remote_branch_refpath)

        if branch_head is None:
            raise ChisubmitException("No such branch: %s" % branch)

        if remote_branch is None:
            raise ChisubmitException("No such remote branch: %s" % branch)

        if self.repo.head.is_detached or self.repo.head.ref != branch_head:
            try:
                branch_head.checkout()
            except GitCommandError, gce:
                print gce
                raise ChisubmitException("Error checking out")

        self.repo.head.reset(remote_branch.commit, index=True, working_tree=True)

    def has_branch(self, branch):
        return (self.__get_branch(branch) is not None)

    def has_remote_branch(self, remote_name, branch):
        return (self.__get_ref("refs/remotes/%s/%s" % (remote_name, branch)) is not None)

    def checkout_branch(self, branch):
        branch_refpath = "refs/heads/%s" % branch
        branch_head = self.__get_head(branch_refpath)

        if branch_head is None:
            raise ChisubmitException("No such branch: %s" % branch)

        try:
            branch_head.checkout()
        except GitCommandError:
            raise ChisubmitException("Error checking out")

    def checkout_commit(self, commit_sha):
        commit = self.get_commit(commit_sha)
        
        if commit is None:
            raise ChisubmitException("Tried to checkout a commit that does not exist: %s" % commit_sha)
        
        try:
            self.repo.git.checkout(commit_sha)
        except GitCommandError:
            raise ChisubmitException("Could not checkout commit %s" % commit_sha)
        

    def get_commit(self, commit_sha):
        try:
            commit = self.repo.commit(commit_sha)
            commit_obj = self.__create_commit_object(commit)
            return commit_obj
        except BadObject, bo:
            return None
        

    def get_tag(self, tag):
        tags = [t for t in self.repo.tags if t.name == tag]

        if len(tags) == 0:
            return None
        else:
            return self.__create_tag_object(tags[0])

    def has_tag(self, tag):
        return (self.get_tag(tag) is not None)

    def create_tag(self, tag_name, commit_sha, message, force = False):
        self.repo.create_tag(tag_name, commit_sha, message, force)

    def create_branch(self, branch, commit):
        self.repo.create_head(branch, commit)

    def push(self, remote_name, branch):
        self.remotes[remote_name].push("%s:%s" % (branch, branch))

    def pull(self, remote_name, branch):
        self.remotes[remote_name].pull("%s" % (branch))
        
    def commit(self, files, commit_message):
        self.repo.index.add(files)
        if self.repo.is_dirty():
            self.repo.index.commit(commit_message)
            return True
        else:
            return False       
    
    def is_dirty(self):
        return self.repo.is_dirty() 

    def __create_tag_object(self, tag):
        return GitTag(name = tag.name,
                      commit = self.__create_commit_object(tag.commit))            


    def __create_commit_object(self, commit):
        authored_date = datetime.datetime.fromtimestamp(commit.authored_date)
        committed_date = datetime.datetime.fromtimestamp(commit.committed_date)
        
        return GitCommit(commit.hexsha, commit.message,
                         commit.author.name, commit.author.email, authored_date, 
                         commit.committer.name, commit.committer.email, committed_date)            
        

    def __get_head(self, path):
        heads = [h for h in self.repo.heads if h.path == path]

        if len(heads) == 0:
            return None
        else:
            return heads[0]

    def __get_branch(self, branch):
        branches = [b for b in self.repo.branches if b.name == branch]

        if len(branches) == 0:
            return None
        else:
            return branches[0]

    def __get_ref(self, path):
        refs = [r for r in self.repo.refs if r.path == path]

        if len(refs) == 0:
            return None
        else:
            return refs[0]
