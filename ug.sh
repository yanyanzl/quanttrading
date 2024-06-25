#comment: update git repository and remote respository after your work
# whole command to be execute: sh ug.sh "git commit message"

git pull
git status
git add *
git commit -a -m "update:$1"
git push
git status

echo "successfully updated your repository! relex and have 
a tea now. message with the update is : $1"
