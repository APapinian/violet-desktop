set -euo pipefail

supply_root=/sys/class/power_supply
state_file=/run/yoga-power-policy/source
ac_profile="$YOGA_AC_PROFILE"
battery_profile="$YOGA_BATTERY_PROFILE"

seen=0
online=0
for supply in "$supply_root"/*; do
    [ -r "$supply/online" ] || continue
    supply_type=''
    if [ -r "$supply/type" ]; then
        IFS= read -r supply_type < "$supply/type" || true
    fi
    [ "$supply_type" != Battery ] || continue
    value=''
    IFS= read -r value < "$supply/online" || true
    case "$value" in
        0) seen=1 ;;
        1) seen=1; online=1 ;;
    esac
done

if [ "$seen" = 0 ]; then
    printf 'Güç kaynağı online bilgisi bulunamadı; mevcut profil korunuyor.\n'
    exit 0
fi

source_kind=battery
desired="$battery_profile"
if [ "$online" = 1 ]; then
    source_kind=ac
    desired="$ac_profile"
fi
signature="$source_kind:$ac_profile:$battery_profile"
previous=''
if [ -r "$state_file" ]; then
    IFS= read -r previous < "$state_file" || true
fi
if [ "$signature" = "$previous" ]; then
    # Aynı kaynak olayı manuel seçimi yeniden yazmaz.
    exit 0
fi

current=$(powerprofilesctl get)
applied="$desired"
if [ "$current" != "$desired" ]; then
    if ! powerprofilesctl set "$desired"; then
        if [ "$desired" != performance ]; then
            printf 'Profil değiştirilemedi: %s\n' "$desired" >&2
            exit 1
        fi
        printf 'Performance seçilemedi; balanced deneniyor.\n' >&2
        powerprofilesctl set balanced
        applied=balanced
    fi
fi

# Başarılı uygulamadan sonra durum kaydedilir. Birim tek seferde bir kez çalışır.
printf '%s\n' "$signature" > "$state_file"
printf 'Güç kaynağı: %s; profil: %s\n' "$source_kind" "$applied"
