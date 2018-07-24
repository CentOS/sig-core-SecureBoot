%global efivar_version 31-1
%global efibootmgr_version 15-1
%global gnu_efi_version 1:3.0.5-9
%global pesign_version 0.109-10

Name:           fwupdate
Version:        9
Release:        8%{?dist}
Summary:        Tools to manage UEFI firmware updates
License:        GPLv2+
URL:            https://github.com/rhinstaller/fwupdate
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
BuildRequires:  efivar-devel >= %{efivar_version}
BuildRequires:  gnu-efi >= %{gnu_efi_version}
BuildRequires:  gnu-efi-devel >= %{gnu_efi_version}
BuildRequires:  pesign >= %{pesign_version}
BuildRequires:  elfutils popt-devel git gettext pkgconfig
BuildRequires:  systemd
ExclusiveArch:  x86_64 aarch64
Source0:        https://github.com/rhinstaller/fwupdate/releases/download/%{name}-%{version}/%{name}-%{version}.tar.bz2
Source1:        securebootca.cer
Source2:        secureboot.cer
Patch0001: 0001-Make-SUBDIRS-overrideable.patch
Patch0002: 0002-efi-fwupdate-make-our-mult-wrapper-get-the-type-of-U.patch
Patch0003: 0003-Nerf-SMBIOS-functions-out-of-fwupdate.patch
Patch0004: 0004-libfwup-get_info-return-whatever-a-second-call-to-ge.patch
Patch0005: 0005-read_file_at-don-t-initialize-saved_errno-if-we-re-n.patch
Patch0006: 0006-fwup_set_up_update-don-t-lseek-on-our-error-path.patch
Patch0007: 0007-add_to_boot_order-actually-always-pass-in-attributes.patch
Patch0008: 0008-fwup_resource_iter_create-make-the-error-path-actual.patch
Patch0009: 0009-add_to_boot_order-set-the-new-BootOrder-entry-at-the.patch
Patch0010: 0010-fwup_set_up_update-check-lseek-s-return-value.patch
Patch0011: 0011-put_info-try-to-limit-bounds-of-our-duplicated-devic.patch
Patch0012: 0012-Try-harder-to-satisfy-coverity-about-the-structure-o.patch
Patch0013: 0013-Add-coverity-makefile-bits.patch
Patch0014: 0014-Don-t-free-alloca-d-memory.patch
Patch0015: 0015-Fix-uninitialized-variable.patch

%ifarch x86_64
%global efiarch x64
%endif
%ifarch aarch64
%global efiarch aa64
%endif

# Figure out the right file path to use
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%description
fwupdate provides a simple command line interface to the UEFI firmware updates.

%package libs
Summary: Library to manage UEFI firmware updates
Requires: %{name}-efi = %{version}-%{release}

%description libs
Library to allow for the simple manipulation of UEFI firmware updates.

%package devel
Summary: Development headers for libfwup
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: efivar-devel >= %{efivar_version}

%description devel
development headers required to use libfwup.

%package efi
Summary: UEFI binaries used by libfwup
Requires: shim

%description efi
UEFI binaries used by libfwup.

%prep
%setup -q -n %{name}-%{version}
git init
git config user.email "%{name}-owner@fedoraproject.org"
git config user.name "Fedora Ninjas"
git add .
git commit -a -q -m "%{version} baseline."
git am %{patches} </dev/null
git config --unset user.email
git config --unset user.name

%build
git config --local --add fwupdate.efidir '%{efidir}'
%ifarch x86_64
setarch linux32 -B make CFLAGS="$RPM_OPT_FLAGS" libdir=%{_libdir} \
        bindir=%{_bindir} EFIDIR=%{efidir} %{?_smp_mflags} \
        SUBDIRS=efi ARCH=ia32
mv -v efi/fwupia32.efi fwupia32.unsigned.efi
%pesign -s -i fwupia32.unsigned.efi -o fwupia32.efi -a %{SOURCE1} -c %{SOURCE2} -n redhatsecureboot301
make clean
%endif
make CFLAGS="$RPM_OPT_FLAGS" libdir=%{_libdir} bindir=%{_bindir} \
     EFIDIR=%{efidir} %{?_smp_mflags}
mv -v efi/fwup%{efiarch}.efi efi/fwup%{efiarch}.unsigned.efi
%pesign -s -i efi/fwup%{efiarch}.unsigned.efi -o efi/fwup%{efiarch}.efi -a %{SOURCE1} -c %{SOURCE2} -n redhatsecureboot301

%install
rm -rf $RPM_BUILD_ROOT
install -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
%make_install EFIDIR=%{efidir} libdir=%{_libdir} \
       bindir=%{_bindir} mandir=%{_mandir} localedir=%{_datadir}/locale/ \
       includedir=%{_includedir} libexecdir=%{_libexecdir} \
       datadir=%{_datadir}
%ifarch x86_64
mv fwupia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
%endif

%ifnarch %{ix86}
%post libs
/sbin/ldconfig
%systemd_post fwupdate-cleanup.service

%preun libs
%systemd_preun fwupdate-cleanup.service

%postun libs
/sbin/ldconfig
%systemd_postun_with_restart pesign.service

%files
%defattr(-,root,root,-)
%{!?_licensedir:%global license %%doc}
%license COPYING
# %%doc README
%{_bindir}/fwupdate
%{_datadir}/locale/en/fwupdate.po
%doc %{_mandir}/man1/*
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/fwupdate

%files devel
%defattr(-,root,root,-)
%doc %{_mandir}/man3/*
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc

%files libs
%defattr(-,root,root,-)
%{_libdir}/*.so.*
%{_datadir}/locale/en/libfwup.po
%{_unitdir}/fwupdate-cleanup.service
%attr(0755,root,root) %dir %{_datadir}/fwupdate/
%config(noreplace) %ghost %{_datadir}/fwupdate/done
%attr(0755,root,root) %dir %{_libexecdir}/fwupdate/
%{_libexecdir}/fwupdate/cleanup
%endif

%files efi
%defattr(-,root,root,-)
%attr(0700,root,root) %dir /boot/efi
%dir /boot/efi/EFI/%{efidir}/
%dir /boot/efi/EFI/%{efidir}/fw/
/boot/efi/EFI/%{efidir}/fwup*.efi

%changelog
* Fri May 19 2017 Peter Jones <pjones@redhat.com> - 9-8
- Hopefully the last TPS related rebuild.
  Related: rhbz#1380825

* Fri May 19 2017 Peter Jones <pjones@redhat.com> - 9-7
- One more TPS related rebuild...
  Related: rhbz#1380825

* Wed May 17 2017 Peter Jones <pjones@redhat.com> - 9-6
- Rebuild to make some dependencies versioned, in order to make TPS's really
  broken builder setup work.
  Related: rhbz#1380825

* Tue May 09 2017 Peter Jones <pjones@redhat.com> - 9-5
- Fix some more coverity issues
  Related: rhbz#1380825

* Mon May 08 2017 Peter Jones <pjones@redhat.com> - 9-4
- Fix some more coverity issues
  Related: rhbz#1380825

* Mon Apr 03 2017 Peter Jones <pjones@redhat.com> - 9-3
- Fix CFLAGS on make invocation
  Related: rhbz#1380825

* Tue Mar 28 2017 Peter Jones <pjones@redhat.com> - 9-2
- Fix a pile of coverity issues.
  Related: rhbz#1380825

* Mon Mar 13 2017 Peter Jones <pjones@redhat.com> - 9-1
- First build in RHEL 7
  Resolves: rhbz#1380825
