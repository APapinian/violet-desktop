if [[ $EUID -ne 0 ]]; then
  echo "Çalıştır: sudo violet-home-snapshot" >&2
  exit 1
fi
exec 9>/run/lock/violet-home-snapshot.lock
flock -n 9 || exit 0
if [[ $(findmnt -n -o FSTYPE --target /home) != btrfs ]]; then
  echo "/home Btrfs değil; anlık görüntü alınmadı." >&2
  exit 1
fi
if [[ $(findmnt -n -o UUID --target /home) != $(findmnt -n -o UUID --target /) ]]; then
  echo "/home ve / farklı disklerde; bu düzen için işlem durduruldu." >&2
  exit 1
fi
btrfs subvolume show /home >/dev/null
snapshot_dir=/.snapshots/hyrule-home
if [[ -L /.snapshots || -L $snapshot_dir ]]; then
  echo "Anlık görüntü hedefi sembolik bağlantı olamaz." >&2
  exit 1
fi
if [[ ! -e /.snapshots ]]; then mkdir -m 700 /.snapshots; fi
mkdir -p "$snapshot_dir"
chmod 700 "$snapshot_dir"
if [[ $(findmnt -n -o UUID --target "$snapshot_dir") != $(findmnt -n -o UUID --target /home) ]]; then
  echo "Anlık görüntü hedefi /home ile aynı Btrfs üzerinde değil." >&2
  exit 1
fi
# Count cap: these are local restore points, not an external backup.
mapfile -t snapshots < <(find "$snapshot_dir" -mindepth 1 -maxdepth 1 -type d \
  -regextype posix-extended -regex '.*/home-[0-9]{8}T[0-9]{6}' | sort)
delete_count=$(( ${#snapshots[@]} - 13 ))
for (( index=0; index<delete_count; index++ )); do
  btrfs subvolume show "${snapshots[index]}" >/dev/null
  btrfs subvolume delete "${snapshots[index]}"
done
available_kib=$(df --output=avail -k /home | tail -n 1 | tr -d ' ')
if (( available_kib < 15 * 1024 * 1024 )); then
  echo "15 GiB'den az boş alan: yeni anlık görüntü atlandı." >&2
  exit 0
fi
target="$snapshot_dir/home-$(date +%Y%m%dT%H%M%S)"
btrfs subvolume snapshot -r /home "$target"
echo "Anlık görüntü: $target (en fazla 14 adet)"
