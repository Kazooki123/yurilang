Name:           yurilang
Version:        1.8.0
Release:        1%{?dist}
Summary:        YuriLang esoteric programming language

License:        GPL3
Requires:       python3, python3-reportlab
Source0:        yurilang.tar.gz

%description
YuriLang programming language.

%install
mkdir -p %{buildroot}/usr/share/yurilang
cp -r * %{buildroot}/usr/share/yurilang

mkdir -p %{buildroot}/usr/bin
echo '#!/bin/sh' > %{buildroot}/usr/bin/yuri
echo 'exec python3 /usr/share/yurilang/yuri.py "$@"' >> %{buildroot}/usr/bin/yuri
chmod +x %{buildroot}/usr/bin/yuri

%files
/usr/bin/yuri
/usr/share/yurilang

%prep
%setup -q
