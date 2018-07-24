%undefine _hardened_build

%global tarversion 2.02~beta2
%undefine _missing_build_ids_terminate_build

Name:           grub2
Epoch:          1
Version:        2.02
Release:        0.65%{?dist}%{?buildid}.2
Summary:        Bootloader with support for Linux, Multiboot and more
Group:          System Environment/Base
License:        GPLv3+
URL:            http://www.gnu.org/software/grub/
Source0:        ftp://alpha.gnu.org/gnu/grub/grub-%{tarversion}.tar.xz
#Source0:	ftp://ftp.gnu.org/gnu/grub/grub-%%{tarversion}.tar.xz
Source1:	grub.macros
Source2:	grub.patches
Source3:	centos.cer
#(source removed)
Source5:	http://unifoundry.com/unifont-5.1.20080820.pcf.gz
Source6:	gitignore

%include %{SOURCE1}

# generate with do-rebase
%include %{SOURCE2}

BuildRequires:  flex bison binutils python
BuildRequires:  ncurses-devel xz-devel bzip2-devel
BuildRequires:  freetype-devel libusb-devel
BuildRequires:	rpm-devel rpm-libs
%ifarch %{sparc} aarch64 ppc64le
# sparc builds need 64 bit glibc-devel - also for 32 bit userland
BuildRequires:  /usr/lib64/crt1.o glibc-static glibc-devel
%else
%ifarch x86_64
BuildRequires:  /usr/lib64/crt1.o glibc-static(x86-64) glibc-devel(x86-64)
# glibc32 is what will be in the buildroots, but glibc-static(x86-32) is what
# will be in an epel-7 (i.e. centos) mock root.  I think.
%if 0%{?centos}%{?mock}
BuildRequires:  /usr/lib/crt1.o glibc-static(x86-32) glibc-devel(x86-32)
%else
BuildRequires:  /usr/lib/crt1.o glibc32
%endif
%else
# ppc64 builds need the ppc crt1.o
BuildRequires:  /usr/lib/crt1.o glibc-static glibc-devel
%endif
%endif
BuildRequires:  autoconf automake autogen device-mapper-devel
BuildRequires:	freetype-devel gettext-devel git
BuildRequires:	texinfo
BuildRequires:	dejavu-sans-fonts
BuildRequires:	help2man
%ifarch %{efi_arch}
BuildRequires:	pesign >= 0.99-8
%endif
%if %{?_with_ccache: 1}%{?!_with_ccache: 0}
BuildRequires:  ccache
%endif

ExcludeArch:	s390 s390x %{arm} %{?ix86}
Obsoletes:	%{name} <= %{flagday}

%if 0%{with_legacy_arch}
Requires:	%{name}-%{legacy_package_arch} = %{evr}
%else
Requires:	%{name}-%{package_arch} = %{evr}
%endif

%global desc \
The GRand Unified Bootloader (GRUB) is a highly configurable and \
customizable bootloader with modular architecture.  It supports a rich \
variety of kernel formats, file systems, computer architectures and \
hardware devices.\
%{nil}

%description
%{desc}

%package common
Summary:	grub2 common layout
Group:		System Environment/Base
BuildArch:	noarch

%description common
This package provides some directories which are required by various grub2
subpackages.

%package tools
Summary:	Support tools for GRUB.
Group:		System Environment/Base
Obsoletes:	%{name}-tools <= %{flagday}
Obsoletes:	%{name}-tools-efi <= %{flagday}
Provides:	%{name}-tools-efi = %{evr}
Requires:	%{name}-tools-minimal = %{evr}
Requires:	%{name}-common = %{evr}
Requires:	gettext os-prober which file
Requires(pre):  dracut
Requires(post): dracut

%description tools
%{desc}
This subpackage provides tools for support of all platforms.

%package tools-minimal
Summary:	Support tools for GRUB.
Group:		System Environment/Base
Requires:	gettext
Requires:	%{name}-common = %{evr}
Obsoletes:	%{name}-tools <= %{flagday}

%description tools-minimal
%{desc}
This subpackage provides tools for support of all platforms.

%package tools-extra
Summary:	Support tools for GRUB.
Group:		System Environment/Base
Requires:	gettext os-prober which file
Requires:	%{name}-tools-minimal = %{epoch}:%{version}-%{release}
Requires:	%{name}-common = %{epoch}:%{version}-%{release}
Requires:	%{name}-tools = %{evr}
Obsoletes:	%{name}-tools <= %{flagday}

%description tools-extra
%{desc}
This subpackage provides tools for support of all platforms.

%if 0%{with_efi_arch}
%define_efi_variant %{package_arch} -p
%endif
%if 0%{with_alt_efi_arch}
%define_efi_variant %{alt_package_arch}
%endif
%if 0%{with_legacy_arch}
%define_legacy_variant %{legacy_package_arch}
%endif

%prep
%setup -T -c -n grub-%{tarversion}
%do_common_setup
# Fix for hardcoded efidir
sed -i.orig -e 's@/efi/EFI/redhat/@/efi/EFI/%{efidir}/@' \
    grub-%{tarversion}/util/grub-setpassword.in
touch --reference=grub-%{tarversion}/util/grub-setpassword.in.orig \
    grub-%{tarversion}/util/grub-setpassword.in
rm -f grub-%{tarversion}/util/grub-setpassword.in.orig

%if 0%{with_efi_arch}
%do_setup %{grubefiarch}
%endif
%if 0%{with_alt_efi_arch}
%do_setup %{grubaltefiarch}
%endif
%if 0%{with_legacy_arch}
%do_setup %{grublegacyarch}
%endif

%build
%if 0%{with_efi_arch}
%do_primary_efi_build %{grubefiarch} %{grubefiname} %{grubeficdname} %{_target_platform} "'%{efi_cflags}'" %{SOURCE3} %{SOURCE3} redhatsecureboot301
%endif
%if 0%{with_alt_efi_arch}
%do_alt_efi_build %{grubaltefiarch} %{grubaltefiname} %{grubalteficdname} %{_alt_target_platform} "'%{alt_efi_cflags}'" %{SOURCE3} %{SOURCE3} redhatsecureboot301
%endif
%if 0%{with_legacy_arch}
%do_legacy_build %{grublegacyarch}
%endif
%do_common_build

%install
set -e
rm -fr $RPM_BUILD_ROOT

%do_common_install
%if 0%{with_efi_arch}
%do_efi_install %{grubefiarch} %{grubefiname} %{grubeficdname}
%endif
%if 0%{with_alt_efi_arch}
%do_alt_efi_install %{grubaltefiarch} %{grubaltefiname} %{grubalteficdname}
%endif
%if 0%{with_legacy_arch}
%do_legacy_install %{grublegacyarch} %{alt_grub_target_name}
%endif
rm -f $RPM_BUILD_ROOT%{_infodir}/dir

%find_lang grub

# Make selinux happy with exec stack binaries.
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/
cat << EOF > ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/grub2.conf
# these have execstack, and break under selinux
-b /usr/bin/grub2-script-check
-b /usr/bin/grub2-mkrelpath
-b /usr/bin/grub2-fstest
-b /usr/sbin/grub2-bios-setup
-b /usr/sbin/grub2-probe
-b /usr/sbin/grub2-sparc64-setup
EOF

# Don't run debuginfo on all the grub modules and whatnot; it just
# rejects them, complains, and slows down extraction.
%global finddebugroot "%{_builddir}/%{?buildsubdir}/debug"

%global dip RPM_BUILD_ROOT=%{finddebugroot} %{__debug_install_post}
%define __debug_install_post (						\
	mkdir -p %{finddebugroot}/usr					\
	mv ${RPM_BUILD_ROOT}/usr/bin %{finddebugroot}/usr/bin		\
	mv ${RPM_BUILD_ROOT}/usr/sbin %{finddebugroot}/usr/sbin		\
	%{dip}								\
	install -m 0755 -d %{buildroot}/usr/lib/ %{buildroot}/usr/src/	\
	cp -al %{finddebugroot}/usr/lib/debug/				\\\
		%{buildroot}/usr/lib/debug/				\
	cp -al %{finddebugroot}/usr/src/debug/				\\\
		%{buildroot}/usr/src/debug/ )				\
	mv %{finddebugroot}/usr/bin %{buildroot}/usr/bin		\
	mv %{finddebugroot}/usr/sbin %{buildroot}/usr/sbin		\
	%{nil}

%clean    
rm -rf $RPM_BUILD_ROOT

%pre tools
if [ -f /boot/grub2/user.cfg ]; then
    if grep -q '^GRUB_PASSWORD=' /boot/grub2/user.cfg ; then
	sed -i 's/^GRUB_PASSWORD=/GRUB2_PASSWORD=/' /boot/grub2/user.cfg
    fi
elif [ -f /boot/efi/EFI/%{efidir}/user.cfg ]; then
    if grep -q '^GRUB_PASSWORD=' /boot/efi/EFI/%{efidir}/user.cfg ; then
	sed -i 's/^GRUB_PASSWORD=/GRUB2_PASSWORD=/' \
	    /boot/efi/EFI/%{efidir}/user.cfg
    fi
elif [ -f /etc/grub.d/01_users ] && \
	grep -q '^password_pbkdf2 root' /etc/grub.d/01_users ; then
    if [ -f /boot/efi/EFI/%{efidir}/grub.cfg ]; then
	# on EFI we don't get permissions on the file, but
	# the directory is protected.
	grep '^password_pbkdf2 root' /etc/grub.d/01_users | \
		sed 's/^password_pbkdf2 root \(.*\)$/GRUB2_PASSWORD=\1/' \
	    > /boot/efi/EFI/%{efidir}/user.cfg
    fi
    if [ -f /boot/grub2/grub.cfg ]; then
	install -m 0600 /dev/null /boot/grub2/user.cfg
	chmod 0600 /boot/grub2/user.cfg
	grep '^password_pbkdf2 root' /etc/grub.d/01_users | \
		sed 's/^password_pbkdf2 root \(.*\)$/GRUB2_PASSWORD=\1/' \
	    > /boot/grub2/user.cfg
    fi
fi

%post tools
if [ "$1" = 1 ]; then
	/sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
	/sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%triggerun -- grub2 < 1:1.99-4
# grub2 < 1.99-4 removed a number of essential files in postun. To fix upgrades
# from the affected grub2 packages, we first back up the files in triggerun and
# later restore them in triggerpostun.
# https://bugzilla.redhat.com/show_bug.cgi?id=735259

# Back up the files before uninstalling old grub2
mkdir -p /boot/grub2.tmp &&
mv -f /boot/grub2/*.mod \
      /boot/grub2/*.img \
      /boot/grub2/*.lst \
      /boot/grub2/device.map \
      /boot/grub2.tmp/ || :

%triggerpostun -- grub2 < 1:1.99-4
# ... and restore the files.
test ! -f /boot/grub2/device.map &&
test -d /boot/grub2.tmp &&
mv -f /boot/grub2.tmp/*.mod \
      /boot/grub2.tmp/*.img \
      /boot/grub2.tmp/*.lst \
      /boot/grub2.tmp/device.map \
      /boot/grub2/ &&
rm -r /boot/grub2.tmp/ || :

%preun tools
if [ "$1" = 0 ]; then
	/sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
	/sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%files

%files common -f grub.lang
%dir %{_libdir}/grub/
%dir %{_datarootdir}/grub/
%dir %{_datarootdir}/grub/themes/
%exclude %{_datarootdir}/grub/themes/*
%attr(0700,root,root) %dir %{_sysconfdir}/grub.d
%dir %{_datarootdir}/grub
%exclude %{_datarootdir}/grub/*
%dir /boot/%{name}
%dir /boot/%{name}/themes/
%dir /boot/%{name}/themes/system
%exclude /boot/%{name}/themes/system/*
%attr(0700,root,root) %dir /boot/grub2
%exclude /boot/grub2/*
%dir %attr(0755,root,root)/boot/efi/EFI/%{efidir}
%exclude /boot/efi/EFI/%{efidir}/*
%license %{common_srcdir}/COPYING
%ghost %config(noreplace) /boot/grub2/grubenv
%doc %{common_srcdir}/INSTALL
%doc %{common_srcdir}/NEWS
%doc %{common_srcdir}/README
%doc %{common_srcdir}/THANKS
%doc %{common_srcdir}/TODO
%doc %{common_srcdir}/docs/grub.html
%doc %{common_srcdir}/docs/grub-dev.html
%doc %{common_srcdir}/docs/font_char_metrics.png
%ifnarch x86_64 %{ix86}
%exclude %{_bindir}/%{name}-render-label
%exclude %{_sbindir}/%{name}-bios-setup
%exclude %{_sbindir}/%{name}-macbless
%endif

%files tools-minimal
%defattr(-,root,root,-)
%{_sysconfdir}/prelink.conf.d/grub2.conf
%{_sbindir}/%{name}-get-kernel-settings
%{_sbindir}/%{name}-set-default
%{_sbindir}/%{name}-setpassword
%{_bindir}/%{name}-editenv
%{_bindir}/%{name}-mkpasswd-pbkdf2

%{_datadir}/man/man3/%{name}-get-kernel-settings*
%{_datadir}/man/man8/%{name}-set-default*
%{_datadir}/man/man8/%{name}-setpassword*
%{_datadir}/man/man1/%{name}-editenv*
%{_datadir}/man/man1/%{name}-mkpasswd-*

%files tools
%defattr(-,root,root,-)
%attr(0644,root,root) %ghost %config(noreplace) %{_sysconfdir}/default/grub
%config %{_sysconfdir}/grub.d/??_*
%{_sysconfdir}/grub.d/README
%{_infodir}/%{name}*
%{_datarootdir}/grub/*
%exclude %{_datarootdir}/grub/themes
%exclude %{_datarootdir}/grub/*.h
%{_datarootdir}/bash-completion/completions/grub
%{_sbindir}/%{name}-install
%{_sbindir}/%{name}-mkconfig
%{_sbindir}/%{name}-probe
%{_sbindir}/%{name}-rpm-sort
%{_sbindir}/%{name}-reboot
%{_bindir}/%{name}-file
%{_bindir}/%{name}-menulst2cfg
%{_bindir}/%{name}-mkrelpath
%{_bindir}/%{name}-script-check
%{_datadir}/man/man?/*

# exclude man pages from tools-extra
%exclude %{_datadir}/man/man8/%{name}-sparc64-setup*
%exclude %{_datadir}/man/man8/%{name}-install*
%exclude %{_datadir}/man/man1/%{name}-fstest*
%exclude %{_datadir}/man/man1/%{name}-glue-efi*
%exclude %{_datadir}/man/man1/%{name}-kbdcomp*
%exclude %{_datadir}/man/man1/%{name}-mkfont*
%exclude %{_datadir}/man/man1/%{name}-mkimage*
%exclude %{_datadir}/man/man1/%{name}-mklayout*
%exclude %{_datadir}/man/man1/%{name}-mknetdir*
%exclude %{_datadir}/man/man1/%{name}-mkrescue*
%exclude %{_datadir}/man/man1/%{name}-mkstandalone*
%exclude %{_datadir}/man/man1/%{name}-syslinux2cfg*

# exclude man pages from tools-minimal
%exclude %{_datadir}/man/man3/%{name}-get-kernel-settings*
%exclude %{_datadir}/man/man8/%{name}-set-default*
%exclude %{_datadir}/man/man8/%{name}-setpassword*
%exclude %{_datadir}/man/man1/%{name}-editenv*
%exclude %{_datadir}/man/man1/%{name}-mkpasswd-*

%ifarch x86_64 %{ix86}
%{_sbindir}/%{name}-macbless
%{_bindir}/%{name}-render-label
%{_datadir}/man/man8/%{name}-macbless*
%{_datadir}/man/man1/%{name}-render-label*
%else
%exclude %{_sbindir}/%{name}-macbless
%exclude %{_bindir}/%{name}-render-label
%exclude %{_datadir}/man/man8/%{name}-macbless*
%exclude %{_datadir}/man/man1/%{name}-render-label*
%endif

%if %{with_legacy_arch}
%{_sbindir}/%{name}-install
%ifarch %{ix86} x86_64
%{_sbindir}/%{name}-bios-setup
%else
%exclude %{_sbindir}/%{name}-bios-setup
%exclude %{_datadir}/man/man8/%{name}-bios-setup*
%endif
%ifarch %{sparc}
%{_sbindir}/%{name}-sparc64-setup
%else
%exclude %{_sbindir}/%{name}-sparc64-setup
%exclude %{_datadir}/man/man8/%{name}-sparc64-setup*
%endif
%ifarch %{sparc} ppc ppc64 ppc64le
%{_sbindir}/%{name}-ofpathname
%else
%exclude %{_sbindir}/%{name}-ofpathname
%exclude %{_datadir}/man/man8/%{name}-ofpathname*
%endif
%endif

%files tools-extra
%{_sbindir}/%{name}-sparc64-setup
%{_sbindir}/%{name}-ofpathname
%{_bindir}/%{name}-fstest
%{_bindir}/%{name}-glue-efi
%{_bindir}/%{name}-kbdcomp
%{_bindir}/%{name}-mkfont
%{_bindir}/%{name}-mkimage
%{_bindir}/%{name}-mklayout
%{_bindir}/%{name}-mknetdir
%ifnarch %{sparc}
%{_bindir}/%{name}-mkrescue
%endif
%{_bindir}/%{name}-mkstandalone
%{_bindir}/%{name}-syslinux2cfg
%{_sysconfdir}/sysconfig/grub
%{_datadir}/man/man8/%{name}-sparc64-setup*
%{_datadir}/man/man8/%{name}-install*
%{_datadir}/man/man1/%{name}-fstest*
%{_datadir}/man/man1/%{name}-glue-efi*
%{_datadir}/man/man1/%{name}-kbdcomp*
%{_datadir}/man/man1/%{name}-mkfont*
%{_datadir}/man/man1/%{name}-mkimage*
%{_datadir}/man/man1/%{name}-mklayout*
%{_datadir}/man/man1/%{name}-mknetdir*
%{_datadir}/man/man1/%{name}-mkrescue*
%{_datadir}/man/man1/%{name}-mkstandalone*
%{_datadir}/man/man8/%{name}-ofpathname*
%{_datadir}/man/man1/%{name}-syslinux2cfg*
%exclude %{_datarootdir}/grub/themes/starfield

%if 0%{with_efi_arch}
%define_efi_variant_files %{package_arch} %{grubefiname} %{grubeficdname} %{grubefiarch} %{target_cpu_name} %{grub_target_name}
%endif
%if 0%{with_alt_efi_arch}
%define_efi_variant_files %{alt_package_arch} %{grubaltefiname} %{grubalteficdname} %{grubaltefiarch} %{alt_target_cpu_name} %{alt_grub_target_name}
%endif
%if 0%{with_legacy_arch}
%define_legacy_variant_files %{legacy_package_arch} %{grublegacyarch}
%endif

%changelog
* Thu Oct 19 2017 CentOS Sources <bugs@centos.org> - 2.02-0.65.el7.centos.2
- Roll in CentOS Secureboot keys
- Move the edidir to be CentOS, so people can co-install fedora, rhel and centos

* Mon Oct 09 2017 Peter Jones <pjones@redhat.com> - 2.02-0.65.el7_4.2
- Fix an incorrect man page exclusion on x86_64.
  Related: rhbz#1499669

* Fri Oct 06 2017 Peter Jones <pjones@redhat.com> - 2.02-0.65.1
- More precise requires and obsoletes on the -tools* subpackages to avoid
  issues with mixing and matching repos the subpackages are split between.
  Resolves: rhbz#1499669

* Tue Oct 03 2017 Peter Jones <pjones@redhat.com> - 2.02-0.65
- Fix spurious : at the end of the mac address netboot paths.
  Resolves: rhbz#1497323

* Wed May 31 2017 Peter Jones <pjones@redhat.com> - 2.02-0.64
- Revert pkglibdir usage; we have to coordinate this with Lorax.
  Related: rhbz#1455243

* Tue May 30 2017 pjones <pjones@redhat.com> - 2.02-0.63
- Fix grub2-mkimage on ppc* to *also* deal with pkglibdir changing.
  Related: rhbz#1455243

* Tue May 30 2017 Peter Jones <pjones@redhat.com> - 2.02-0.62
- Fix grub2-mkimage on ppc* to *also* deal with pkglibdir changing.
  Related: rhbz#1455243

* Wed May 24 2017 Peter Jones <pjones@redhat.com> - 2.02-0.61
- Fix some minor ia32 booting bugs
  Related: rhbz#1310763
  Related: rhbz#1411748
  Related: rhbz#1300009
- Add support for non-Ethernet network cards
  Related: rhbz#1232432
- Add support for http booting
  Resolves: rhbz#1232432
- Fix efi module subpackage obsoletes/provides
  Resolves: rhbz#1447723
- Make ppc modules subpackages use different directories on the filesystem.
  Resolves: rhbz#1455243

* Thu Apr 20 2017 Peter Jones <pjones@redhat.com> - 2.02-0.60
- Fix ppc64 deciding /boot/efi might somehow be the CHRP partition if it
  exists.  This is also why the bug we fixed in 0.59 showed up at all.
  Resolves: rhbz#1443809
  Resolves: rhbz#1442970
- Fix a regexp problem where rpm spec parser un-escapes things that
  don't need escaping, which causes our s/-mcpu=power8/-mcpu=power6/
  to fail.
  Related: rhbz#1443809

* Wed Apr 19 2017 Peter Jones <pjones@redhat.com> - 2.02-0.59
- Fix ppc64 "grub2.chrp" to be "grub.chrp" harder
  Resolves: rhbz#1442970

* Wed Apr 19 2017 Peter Jones <pjones@redhat.com> - 2.02-0.58
- Add Aarch64 FDT #address-cells and #size-cells support
  Resolves: rhbz#1436745
- Fix ppc64 "grub2.chrp" to be "grub.chrp"
  Resolves: rhbz#1442970

* Wed Apr 12 2017 Peter Jones <pjones@redhat.com> - 2.02-0.57
- Make "grub2" require the grub2-efi-... package on arches where there's no
  legacy build.
  Related: rhbz#1440787

* Tue Apr 11 2017 Peter Jones <pjones@redhat.com> - 2.02-0.56
- Rebuild in the right build root.
  Related: rhbz#1437450

* Tue Apr 11 2017 Peter Jones <pjones@redhat.com> - 2.02-0.55
- Make a "grub2" top-level package to help solve Jira RCM-14929.
  Related: rhbz#1437450

* Mon Apr 10 2017 Peter Jones <pjones@redhat.com> - 2.02-0.54
- Make grub2-pc, grub2-ppc64le, etc, also have an Obsoletes for the old grub2
  packages.  Hoping this will solve Jira RCM-14929.
  Related: rhbz#1437450

* Thu Mar 30 2017 Peter Jones <pjones@redhat.com> - 2.02-0.53
- Don't manually put an arch in a requires.
  The automatically generated provides won't have it, and all of the
  tools display the packages as if it were there, so you can't ever see
  that they never match up. Meanwhile the auto generator *will* add
  $name($arch)=$evr provides, which aren't quite the same.  We probably
  don't need it anyway.  Maybe.
  Resolves: rhbz#1437450

* Thu Mar 30 2017 Peter Jones <pjones@redhat.com> - 2.02-0.52
- Fix our debuginfo filter to not accidentally discard the stripped versions of
  userland binaries.
  Related: rhbz#1310763

* Tue Mar 28 2017 Peter Jones <pjones@redhat.com> - 2.02-0.51
- Also be sure to pull in grub2-tools-extras for now, to make upgrades work.
  Related: rhbz#1310763

* Tue Mar 28 2017 Peter Jones <pjones@redhat.com> - 2.02-0.50
- Fix where the grub2-ofpathname man page lands
  Related: rhbz#1310763
- Fix stripping of userland binaries
  Related: rhbz#1310763

* Tue Mar 21 2017 Peter Jones <pjones@redhat.com> - 2.02-0.49
- Include unicode.pf2 in the grub-efi-ARCH-cdboot images
  Related: rhbz#1310763
  Related: rhbz#1411748
  Related: rhbz#1300009

* Tue Mar 21 2017 Peter Jones <pjones@redhat.com> - 2.02-0.48
- grub2-efi-* don't actually need to require grub2-tools-efi (i.e. the mac
  tools), anaconda and lorax can know how to do that.
  Related: rhbz#1310763
  Related: rhbz#1411748
  Related: rhbz#1300009

* Mon Mar 20 2017 Peter Jones <pjones@redhat.com> - 2.02-0.47
- Fix ia32 booting.
  Related: rhbz#1310763
  Related: rhbz#1411748
  Related: rhbz#1300009

* Fri Mar 17 2017 Peter Jones <pjones@redhat.com> - 2.02-0.46
- Fix ppc* package names.
  Related: rhbz#1310763
  Related: rhbz#1411748
  Related: rhbz#1300009

* Wed Mar 15 2017 Peter Jones <pjones@redhat.com> - 2.02-0.45
- Rework package to make multi-arch EFI easier.
  Resolves: rhbz#1310763
  Related: rhbz#1411748
- Honor IO alignment on EFI systems
  Resolves: rhbz#1300009

* Mon Aug 29 2016 Peter Jones <pjones@redhat.com> - 2.02-0.44
- Work around tftp servers that don't work with multiple consecutive slashes in
  file paths.
  Resolves: rhbz#1217243

* Thu Aug 25 2016 Peter Jones <pjones@redhat.com> - 2.02-0.42
- Make grub2-mkconfig export grub2-get-kernel-settings variables correctly.
  Related: rhbz#1226325

* Tue Aug 23 2016 Peter Jones <pjones@redhat.com> - 2.02-0.42
- Rebuild in the right build root.  Again.
  Related: rhbz#1273974

* Wed Jul 13 2016 Peter Jones <pjones@redhat.com> - 2.02-0.41
- Build with coverity patch I missed last time.
  Related: rhbz#1226325

* Wed Jul 13 2016 rmarshall@redhat.com - 2.02-0.40
- Build with coverity patches.
  Related: rhbz#1226325

* Wed Jul 13 2016 Peter Jones <pjones@redhat.com>
- Remove our patch to force a paricular uefi network interface
  Related: rhbz#1273974
  Related: rhbz#1277599
  Related: rhbz#1298765
- Update some more coverity issues
  Related: rhbz#1226325
  Related: rhbz#1154226

* Mon Jul 11 2016 rmarshall@redhat.com - 2.02-0.39
- Fix all issues discovered during coverity scan. 
  Related: rhbz#1154226
- Fix a couple compiler and CLANG issues discovered during coverity scan.
  Related: rhbz#1154226
- Fix the last few CLANG issues and a deadcode issue discovered by the
  coverity scan.
  Related: rhbz#1154226

* Fri Jul 01 2016 Peter Jones <pjones@redhat.com> - 2.02-0.38
- Pick the right build target.  Again.
  Related: rhbz#1226325

* Tue Jun 21 2016 rmarshall@redhat.com - 2.02-0.37
- Update fix for rhbz#1212114 to reflect the move to handling this case
  in anaconda.
  Related: rhbz#1315468
  Resolves: rhbz#1261926
- Add grub2-get-kernel-settings to allow grub2-mkconfig to take grubby
  configuration changes into account.
  Resolves: rhbz#1226325

* Fri Jun 17 2016 Peter Jones <pjones@redhat.com> - 2.02-0.36
- Better support for EFI network booting with dhcpv6.
  Resolves: rhbz#1154226
- Back out a duplicate change resulting in some EFI network firmware drivers
  not working properly.
  Related: rhbz#1273974
  Related: rhbz#1277599
  Related: rhbz#1298765

* Mon Jun 06 2016 Peter Jones <pjones@redhat.com> - 2.02-0.35
- Don't use legacy methods to make device node variables.
  Resolves: rhbz#1279599
- Don't pad initramfs with zeros
  Resolves: rhbz#1219864

* Thu Apr 28 2016 rmarshall@redhat.com 2.02-0.34
- Exit grub-mkconfig with a proper code when the new configuration would be
  invalid.
  Resolves: rhbz#1252311
- Warn users if grub-mkconfig needs to be run to add support for GRUB
  passwords.
  Resolves: rhbz#1290803
- Fix the information in the --help and man pages for grub-setpassword
  Resolves: rhbz#1290799
- Fix issue where shell substitution expected non-translated output when
  setting a bootloader password.
  Resolves: rhbz#1294243
- Fix an issue causing memory regions with unknown types to be marked available
  through a series of backports from upstream.
  Resolves: rhbz#1288608

* Thu Dec 10 2015 Peter Jones <pjones@redhat.com> - 2.02-0.33
- Don't remove 01_users, it's the wrong thing to do.
  Related: rhbz#1284370

* Wed Dec 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.32
- Rebuild for .z so the release number is different.
  Related: rhbz#1284370

* Wed Dec 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.31
- More work on handling of GRUB2_PASSWORD
  Resolves: rhbz#1284370

* Tue Dec 08 2015 Peter Jones <pjones@redhat.com> - 2.02-0.30
- Fix security issue when reading username and password
  Resolves: CVE-2015-8370
- Do a better job of handling GRUB_PASSWORD
  Resolves: rhbz#1284370

* Fri Oct 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.29
- Fix DHCP6 timeouts due to failed network stack once more.
  Resolves: rhbz#1267139

* Thu Sep 17 2015 Peter Jones <pjones@redhat.com> - 2.02-0.28
- Once again, rebuild for the right build target.
  Resolves: CVE-2015-5281

* Thu Sep 17 2015 Peter Jones <pjones@redhat.com> - 2.02-0.27
- Remove multiboot and multiboot2 modules from the .efi builds; they
  should never have been there.
  Resolves: CVE-2015-5281

* Mon Sep 14 2015 Peter Jones <pjones@redhat.com> - 2.02-0.26
- Be more aggressive about trying to make sure we use the configured SNP
  device in UEFI.
  Resolves: rhbz#1257475

* Wed Aug 05 2015 Robert Marshall <rmarshall@redhat.com> - 2.02-0.25
- Force file sync to disk on ppc64le machines.
  Resolves: rhbz#1212114

* Mon Aug 03 2015 Peter Jones <pjones@redhat.com> - 2.02-0.24
- Undo 0.23 and fix it a different way.
  Resolves: rhbz#1124074

* Thu Jul 30 2015 Peter Jones <pjones@redhat.com> - 2.02-0.23
- Reverse kernel sort order so they're displayed correctly.
  Resolves: rhbz#1124074

* Wed Jul 08 2015 Peter Jones <pjones@redhat.com> - 2.02-0.22
- Make upgrades work reasonably well with grub2-setpassword .
  Related: rhbz#985962

* Tue Jul 07 2015 Peter Jones <pjones@redhat.com> - 2.02-0.21
- Add a simpler grub2 password config tool
  Related: rhbz#985962
- Some more coverity nits.

* Mon Jul 06 2015 Peter Jones <pjones@redhat.com> - 2.02-0.20
- Deal with some coverity nits.
  Related: rhbz#1215839
  Related: rhbz#1124074

* Mon Jul 06 2015 Peter Jones <pjones@redhat.com> - 2.02-0.19
- Rebuild for Aarch64
- Deal with some coverity nits.
  Related: rhbz#1215839
  Related: rhbz#1124074

* Thu Jul 02 2015 Peter Jones <pjones@redhat.com> - 2.02-0.18
- Update for an rpmdiff problem with one of the man pages.
  Related: rhbz#1124074

* Tue Jun 30 2015 Peter Jones <pjones@redhat.com> - 2.02-0.17
- Handle ipv6 better
  Resolves: rhbz#1154226
- On UEFI, use SIMPLE_NETWORK_PROTOCOL when we can.
  Resolves: rhbz#1233378
- Handle rssd disk drives in grub2 utilities.
  Resolves: rhbz#1087962
- Handle xfs CRC disk format.
  Resolves: rhbz#1001279
- Calibrate TCS using the EFI Stall service
  Resolves: rhbz#1150698
- Fix built-in gpg verification when using TFTP
  Resolves: rhbz#1167977
- Generate better stanza titles so grubby can find them easier.
  Resolves: rhbz#1177003
- Don't strip the fw_path variable twice when we're using EFI networking.
  Resolves: rhbz#1211101

* Mon May 11 2015 Peter Jones <pjones@redhat.com> - 2.02-0.17
- Document network boot paths better
  Resolves: rhbz#1148650
- Use an rpm-based version sorted in grub2-mkconfig
  Resolves: rhbz#1124074

* Thu Oct 09 2014 Peter Jones <pjones@redhat.com> - 2.02-0.16
- ... and build it on the right target.
  Related: rhbz#1148652

* Thu Oct 09 2014 Peter Jones <pjones@redhat.com> - 2.02-0.15
- Make netbooting do a better job of picking the config path *again*.
  Resolves: rhbz#1148652

* Sat Oct 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.14
- Be sure to *install* gcdaa64.efi
  Related: rhbz#1100048

* Fri Sep 26 2014 Peter Jones <pjones@redhat.com> - 2.02-0.13
- Make sure to build a gcdaa64.efi
  Related: rhbz#1100048

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 2.02-0.12
- Fix minor problems rpmdiff found.
  Related: rhbz#1125540

* Mon Sep 22 2014 Peter Jones <pjones@redhat.com> - 2.02-0.11
- Fix grub2 segfault when root isn't set.
  Resolves: rhbz#1084536
- Make the aarch64 loader be SB-aware.
  Related: rhbz#1100048
- Enable regexp module
  Resolves: rhbz#1125916

* Thu Sep 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.10
- Make editenv utilities (grub2-editenv, grub2-set-default, etc.) from
  non-UEFI builds work with UEFI builds as well, since they're shared
  from grub2-tools.
  Resolves: rhbz#1119943
- Make more grub2-mkconfig generate menu entries with the OS name and version
  included.
  Resolves: rhbz#996794
- Minimize the sort ordering for .debug and -rescue- kernels.
  Resolves: rhbz#1065360
- Add GRUB_DISABLE_UUID to disable filesystem searching by UUID.
  Resolves: rhbz#1027833
- Allow "fallback" to specify titles like the documentation says
  Resolves: rhbz#1026084

* Wed Aug 27 2014 Peter Jones <pjones@redhat.com> - 2.02-0.9.1
- A couple of patches for aarch64 got missed.
  Related: rhbz#967937

* Wed Aug 27 2014 Peter Jones <pjones@redhat.com> - 2.02-0.9
- Once again, I have built with the wrong target.
  Related: rhbz#1125540
  Resolves: rhbz#967937

* Fri Aug 22 2014 Peter Jones <pjones@redhat.com> - 2.02-0.8
- Add patches for ppc64le
  Related: rhbz#1125540

* Thu Mar 20 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.10
- Fix GRUB_DISABLE_SUBMENU one more time.
  Resolves: rhbz#1063414

* Tue Mar 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.9
- Not sure why the right build target wasn't used *again*.
  Resolves: rhbz#1073337

* Wed Mar 12 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.8
- Make GRUB_DISABLE_SUBMENU work again.
  Resolves: rhbz#1063414

* Thu Mar 06 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.7
- Build on the right target.
  Resolves: rhbz#1073337

* Wed Mar 05 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.6
- Fix minor man page install bug
  Related: rhbz#948847

* Tue Mar 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.5
- Add man pages for common grub utilities.
  Resolves: rhbz#948847
- Fix shift key behavior on UEFI.
  Resolves: rhbz#1068215

* Tue Feb 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.4
- Build against the right target.
  Related: rhbz#1064424

* Tue Feb 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.3
- Don't emit "Booting <foo>" message.
  Resolves: rhbz#1023142
- Don't require a password for booting, only for editing entries.
  Resolves: rhbz#1030176
- Several network fixes from IBM
  Resolves: rhbz#1056324
- Support NVMe device names
  Resolves: rhbz#1019660
- Make control keys work on UEFI systems.
  Resolves: rhbz#1056035

* Fri Jan 31 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.2
- Fix FORTIFY_SOURCE for util/
  Related: rhbz#1049047

* Tue Jan 21 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.1
- Don't destroy symlinks when re-writing grub.cfg
  Resolves: rhbz#1032182

* Mon Jan 06 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2
- Update to grub-2.02~beta2

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1:2.00-23
- Mass rebuild 2013-12-27

* Wed Nov 20 2013 Peter Jones <pjones@redhat.com> - 2.00-22.10
- Rebuild with correct release number and with correct target.
  Related: rhbz#1032530

* Wed Nov 20 2013 Daniel Mach <dmach@redhat.com> - 2.00-22.9.1
- Enable tftp module
  Resolves: rhbz#1032530

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 2.00-22.9
- Make "linux16" happen on x86_64 machines as well.
  Resolves: rhbz#880840

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 2.00-22.8
- Rebuild with correct build target for signing.
  Related: rhbz#996863

* Tue Nov 05 2013 Peter Jones <pjones@redhat.com> - 2.00-22.7
- Build with -mcpu=power6 as we did before redhat-rpm-config changed
  Resolves: rhbz#1026368

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.6
- Make linux16 work with the shell better.
  Resolves: rhbz#880840

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.5
- Rebuild because we were clobbering signing in the spec file...
  Related: rhbz#1017855

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.4
- Rebuild because signing didn't work.
  Related: rhbz#1017855

* Mon Oct 28 2013 Peter Jones <pjones@redhat.com> - 2.00-22.3
- Use linux16 when appropriate:
  Resolves: rhbz#880840
- Enable pager by default:
  Resolves: rhbz#985860
- Don't ask the user to hit keys that won't work.
  Resolves: rhbz#987443
- Sign grub2 during builds
  Resolves: rhbz#1017855

* Thu Aug 29 2013 Peter Jones <pjones@redhat.com> - 2.00-22.2
- Fix minor rpmdiff complaints.

* Wed Aug 07 2013 Peter Jones <pjones@redhat.com> - 2.00-22.1
- Fix url so PkgWrangler doesn't go crazy.

* Fri Jun 21 2013 Peter Jones <pjones@redhat.com> - 2.00-22
- Fix linewrapping in edit menu.
  Resolves: rhbz #976643

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 2.00-21
- Fix obsoletes to pull in -starfield-theme subpackage when it should.

* Fri Jun 14 2013 Peter Jones <pjones@redhat.com> - 2.00-20
- Put the theme entirely ento the subpackage where it belongs (#974667)

* Wed Jun 12 2013 Peter Jones <pjones@redhat.com> - 2.00-19
- Rebase to upstream snapshot.
- Fix PPC build error (#967862)
- Fix crash on net_bootp command (#960624)
- Reset colors on ppc when appropriate (#908519)
- Left align "Loading..." messages (#908492)
- Fix probing of SAS disks on PPC (#953954)
- Add support for UEFI OSes returned by os-prober
- Disable "video" mode on PPC for now (#973205)
- Make grub fit better into the boot sequence, visually (#966719)

* Fri May 10 2013 Matthias Clasen <mclasen@redhat.com> - 2.00-18
- Move the starfield theme to a subpackage (#962004)
- Don't allow SSE or MMX on UEFI builds (#949761)

* Wed Apr 24 2013 Peter Jones <pjones@redhat.com> - 2.00-17.pj0
- Rebase to upstream snapshot.

* Thu Apr 04 2013 Peter Jones <pjones@redhat.com> - 2.00-17
- Fix booting from drives with 4k sectors on UEFI.
- Move bash completion to new location (#922997)
- Include lvm support for /boot (#906203)

* Thu Feb 14 2013 Peter Jones <pjones@redhat.com> - 2.00-16
- Allow the user to disable submenu generation
- (partially) support BLS-style configuration stanzas.

* Tue Feb 12 2013 Peter Jones <pjones@redhat.com> - 2.00-15.pj0
- Add various config file related changes.

* Thu Dec 20 2012 Dennis Gilmore <dennis@ausil.us> - 2.00-15
- bump nvr

* Mon Dec 17 2012 Karsten Hopp <karsten@redhat.com> 2.00-14
- add bootpath device to the device list (pfsmorigo, #886685)

* Tue Nov 27 2012 Peter Jones <pjones@redhat.com> - 2.00-13
- Add vlan tag support (pfsmorigo, #871563)
- Follow symlinks during PReP installation in grub2-install (pfsmorigo, #874234)
- Improve search paths for config files on network boot (pfsmorigo, #873406)

* Tue Oct 23 2012 Peter Jones <pjones@redhat.com> - 2.00-12
- Don't load modules when grub transitions to "normal" mode on UEFI.

* Mon Oct 22 2012 Peter Jones <pjones@redhat.com> - 2.00-11
- Rebuild with newer pesign so we'll get signed with the final signing keys.

* Thu Oct 18 2012 Peter Jones <pjones@redhat.com> - 2.00-10
- Various PPC fixes.
- Fix crash fetching from http (gustavold, #860834)
- Issue separate dns queries for ipv4 and ipv6 (gustavold, #860829)
- Support IBM CAS reboot (pfsmorigo, #859223)
- Include all modules in the core image on ppc (pfsmorigo, #866559)

* Mon Oct 01 2012 Peter Jones <pjones@redhat.com> - 1:2.00-9
- Work around bug with using "\x20" in linux command line.
  Related: rhbz#855849

* Thu Sep 20 2012 Peter Jones <pjones@redhat.com> - 2.00-8
- Don't error on insmod on UEFI/SB, but also don't do any insmodding.
- Increase device path size for ieee1275
  Resolves: rhbz#857936
- Make network booting work on ieee1275 machines.
  Resolves: rhbz#857936

* Wed Sep 05 2012 Matthew Garrett <mjg@redhat.com> - 2.00-7
- Add Apple partition map support for EFI

* Thu Aug 23 2012 David Cantrell <dcantrell@redhat.com> - 2.00-6
- Only require pesign on EFI architectures (#851215)

* Tue Aug 14 2012 Peter Jones <pjones@redhat.com> - 2.00-5
- Work around AHCI firmware bug in efidisk driver.
- Move to newer pesign macros
- Don't allow insmod if we're in secure-boot mode.

* Wed Aug 08 2012 Peter Jones <pjones@redhat.com>
- Split module lists for UEFI boot vs UEFI cd images.
- Add raid modules for UEFI image (related: #750794)
- Include a prelink whitelist for binaries that need execstack (#839813)
- Include fix efi memory map fix from upstream (#839363)

* Wed Aug 08 2012 Peter Jones <pjones@redhat.com> - 2.00-4
- Correct grub-mkimage invocation to use efidir RPM macro (jwb)
- Sign with test keys on UEFI systems.
- PPC - Handle device paths with commas correctly.
  Related: rhbz#828740

* Wed Jul 25 2012 Peter Jones <pjones@redhat.com> - 2.00-3
- Add some more code to support Secure Boot, and temporarily disable
  some other bits that don't work well enough yet.
  Resolves: rhbz#836695

* Wed Jul 11 2012 Matthew Garrett <mjg@redhat.com> - 2.00-2
- Set a prefix for the image - needed for installer work
- Provide the font in the EFI directory for the same reason

* Thu Jun 28 2012 Peter Jones <pjones@redhat.com> - 2.00-1
- Rebase to grub-2.00 release.

* Mon Jun 18 2012 Peter Jones <pjones@redhat.com> - 2.0-0.37.beta6
- Fix double-free in grub-probe.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.36.beta6
- Build with patch19 applied.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.35.beta6
- More ppc fixes.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.34.beta6
- Add IBM PPC fixes.

* Mon Jun 04 2012 Peter Jones <pjones@redhat.com> - 2.0-0.33.beta6
- Update to beta6.
- Various fixes from mads.

* Fri May 25 2012 Peter Jones <pjones@redhat.com> - 2.0-0.32.beta5
- Revert builddep change for crt1.o; it breaks ppc build.

* Fri May 25 2012 Peter Jones <pjones@redhat.com> - 2.0-0.31.beta5
- Add fwsetup command (pjones)
- More ppc fixes (IBM)

* Tue May 22 2012 Peter Jones <pjones@redhat.com> - 2.0-0.30.beta5
- Fix the /other/ grub2-tools require to include epoch.

* Mon May 21 2012 Peter Jones <pjones@redhat.com> - 2.0-0.29.beta5
- Get rid of efi_uga and efi_gop, favoring all_video instead.

* Mon May 21 2012 Peter Jones <pjones@redhat.com> - 2.0-0.28.beta5
- Name grub.efi something that's arch-appropriate (kiilerix, pjones)
- use EFI/$SOMETHING_DISTRO_BASED/ not always EFI/redhat/grub2-efi/ .
- move common stuff to -tools (kiilerix)
- spec file cleanups (kiilerix)

* Mon May 14 2012 Peter Jones <pjones@redhat.com> - 2.0-0.27.beta5
- Fix module trampolining on ppc (benh)

* Thu May 10 2012 Peter Jones <pjones@redhat.com> - 2.0-0.27.beta5
- Fix license of theme (mizmo)
  Resolves: rhbz#820713
- Fix some PPC bootloader detection IBM problem
  Resolves: rhbz#820722

* Thu May 10 2012 Peter Jones <pjones@redhat.com> - 2.0-0.26.beta5
- Update to beta5.
- Update how efi building works (kiilerix)
- Fix theme support to bring in fonts correctly (kiilerix, pjones)

* Wed May 09 2012 Peter Jones <pjones@redhat.com> - 2.0-0.25.beta4
- Include theme support (mizmo)
- Include locale support (kiilerix)
- Include html docs (kiilerix)

* Thu Apr 26 2012 Peter Jones <pjones@redhat.com> - 2.0-0.24
- Various fixes from Mads Kiilerich

* Thu Apr 19 2012 Peter Jones <pjones@redhat.com> - 2.0-0.23
- Update to 2.00~beta4
- Make fonts work so we can do graphics reasonably

* Thu Mar 29 2012 David Aquilina <dwa@redhat.com> - 2.0-0.22
- Fix ieee1275 platform define for ppc

* Thu Mar 29 2012 Peter Jones <pjones@redhat.com> - 2.0-0.21
- Remove ppc excludearch lines (dwa)
- Update ppc terminfo patch (hamzy)

* Wed Mar 28 2012 Peter Jones <pjones@redhat.com> - 2.0-0.20
- Fix ppc64 vs ppc exclude according to what dwa tells me they need
- Fix version number to better match policy.

* Tue Mar 27 2012 Dan Horák <dan[at]danny.cz> - 1.99-19.2
- Add support for serial terminal consoles on PPC by Mark Hamzy

* Sun Mar 25 2012 Dan Horák <dan[at]danny.cz> - 1.99-19.1
- Use Fix-tests-of-zeroed-partition patch by Mark Hamzy

* Thu Mar 15 2012 Peter Jones <pjones@redhat.com> - 1.99-19
- Use --with-grubdir= on configure to make it behave like -17 did.

* Wed Mar 14 2012 Peter Jones <pjones@redhat.com> - 1.99-18
- Rebase from 1.99 to 2.00~beta2

* Wed Mar 07 2012 Peter Jones <pjones@redhat.com> - 1.99-17
- Update for newer autotools and gcc 4.7.0
  Related: rhbz#782144
- Add /etc/sysconfig/grub link to /etc/default/grub
  Resolves: rhbz#800152
- ExcludeArch s390*, which is not supported by this package.
  Resolves: rhbz#758333

* Fri Feb 17 2012 Orion Poplawski <orion@cora.nwra.com> - 1:1.99-16
- Build with -Os (bug 782144)

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.99-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Dec 14 2011 Matthew Garrett <mjg@redhat.com> - 1.99-14
- fix up various grub2-efi issues

* Thu Dec 08 2011 Adam Williamson <awilliam@redhat.com> - 1.99-13
- fix hardwired call to grub-probe in 30_os-prober (rhbz#737203)

* Mon Nov 07 2011 Peter Jones <pjones@redhat.com> - 1.99-12
- Lots of .spec fixes from Mads Kiilerich:
  Remove comment about update-grub - it isn't run in any scriptlets
  patch info pages so they can be installed and removed correctly when renamed
  fix references to grub/grub2 renames in info pages (#743964)
  update README.Fedora (#734090)
  fix comments for the hack for upgrading from grub2 < 1.99-4
  fix sed syntax error preventing use of $RPM_OPT_FLAGS (#704820)
  make /etc/grub2*.cfg %config(noreplace)
  make grub.cfg %ghost - an empty file is of no use anyway
  create /etc/default/grub more like anaconda would create it (#678453)
  don't create rescue entries by default - grubby will not maintain them anyway
  set GRUB_SAVEDEFAULT=true so saved defaults works (rbhz#732058)
  grub2-efi should have its own bash completion
  don't set gfxpayload in efi mode - backport upstream r3402
- Handle dmraid better. Resolves: rhbz#742226

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.99-11
- Rebuilt for glibc bug#747377

* Wed Oct 19 2011 Adam Williamson <awilliam@redhat.com> - 1.99-10
- /etc/default/grub is explicitly intended for user customization, so
  mark it as config(noreplace)

* Tue Oct 11 2011 Peter Jones <pjones@redhat.com> - 1.99-9
- grub has an epoch, so we need that expressed in the obsolete as well.
  Today isn't my day.

* Tue Oct 11 2011 Peter Jones <pjones@redhat.com> - 1.99-8
- Fix my bad obsoletes syntax.

* Thu Oct 06 2011 Peter Jones <pjones@redhat.com> - 1.99-7
- Obsolete grub
  Resolves: rhbz#743381

* Wed Sep 14 2011 Peter Jones <pjones@redhat.com> - 1.99-6
- Use mv not cp to try to avoid moving disk blocks around for -5 fix
  Related: rhbz#735259
- handle initramfs on xen better (patch from Marko Ristola)
  Resolves: rhbz#728775

* Sat Sep 03 2011 Kalev Lember <kalevlember@gmail.com> - 1.99-5
- Fix upgrades from grub2 < 1.99-4 (#735259)

* Fri Sep 02 2011 Peter Jones <pjones@redhat.com> - 1.99-4
- Don't do sysadminny things in %preun or %post ever. (#735259)
- Actually include the changelog in this build (sorry about -3)

* Thu Sep 01 2011 Peter Jones <pjones@redhat.com> - 1.99-2
- Require os-prober (#678456) (patch from Elad Alfassa)
- Require which (#734959) (patch from Elad Alfassa)

* Thu Sep 01 2011 Peter Jones <pjones@redhat.com> - 1.99-1
- Update to grub-1.99 final.
- Fix crt1.o require on x86-64 (fix from Mads Kiilerich)
- Various CFLAGS fixes (from Mads Kiilerich)
  - -fexceptions and -m64
- Temporarily ignore translations (from Mads Kiilerich)

* Thu Jul 21 2011 Peter Jones <pjones@redhat.com> - 1.99-0.3
- Use /sbin not /usr/sbin .

* Thu Jun 23 2011 Peter Lemenkov <lemenkov@gmail.com> - 1:1.99-0.2
- Fixes for ppc and ppc64

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.98-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild
