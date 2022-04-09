DIR="$HOME/MyDino"
REPOSITORY="https://github.com/PetrusBellmonte/MyDino"
if ! [ -d "$DIR" ]; then
  echo "Installing files in ${DIR}..."
  git clone $REPOSITORY "$DIR"
fi
cd "$DIR" || exit 1
git pull  | grep -q -v 'Already up to date.' && CHANGED=1
if [ $CHANGED ]; then
  systemctl restart dinoclient.service
fi