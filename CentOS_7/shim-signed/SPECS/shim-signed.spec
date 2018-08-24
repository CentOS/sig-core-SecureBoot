Name:           shim-signed
Version:        12
Release:        1%{?dist}%{?buildid}
Summary:        First-stage UEFI bootloader
%define unsigned_release 1%{?dist}

License:        BSD
URL:            http://www.codon.org.uk/~mjg59/shim/
# incorporate mokutil for packaging simplicity
%global mokutil_version 0.3.0
Source0:        https://github.com/lcp/mokutil/archive/mokutil-%{mokutil_version}.tar.gz
Patch0001: 0001-Fix-the-potential-buffer-overflow.patch
Patch0002: 0002-Fix-the-32bit-signedness-comparison.patch
Patch0003: 0003-Build-with-fshort-wchar-so-toggle-passwords-work-rig.patch
Patch0004: 0004-Don-t-allow-sha1-on-the-mokutil-command-line.patch
Patch0005: 0005-Make-all-efi_guid_t-const.patch
Patch0006: 0006-mokutil-be-explicit-about-file-modes-in-all-cases.patch
Patch0007: 0007-Add-bash-completion-file.patch

Source1:	centos.crt
Source10:	shimx64.efi
Source11:	shimia32.efi
#Source12:	shimaa64.efi
Source20:	BOOTX64.CSV
Source21:	BOOTIA32.CSV
Source22:	BOOTAA64.CSV

%ifarch x86_64
%global efiarch X64
%global efiarchlc x64
%global shimsrc %{SOURCE10}
%global bootsrc %{SOURCE20}

%global shimsrcia32 %{SOURCE11}
%global bootsrcia32 %{SOURCE21}
%define unsigned_dir_ia32 %{_datadir}/shim/ia32-%{version}-%{unsigned_release}/
%endif
%ifarch aarch64
%global efiarch AA64
%global efiarchlc aa64
#%global shimsrc %{SOURCE12}
%global bootsrc %{SOURCE22}
%endif
%define unsigned_dir %{_datadir}/shim/%{efiarchlc}-%{version}-%{unsigned_release}/

BuildRequires: git
BuildRequires: openssl-devel openssl
BuildRequires: pesign >= 0.106-5%{dist}
BuildRequires: efivar-devel
BuildRequires: shim-unsigned-%{efiarchlc} = %{version}-%{unsigned_release}
%ifarch x86_64
BuildRequires: shim-unsigned-ia32 = %{version}-%{unsigned_release}
%endif

# for mokutil's configure
BuildRequires: autoconf automake

# Shim is only required on platforms implementing the UEFI secure boot
# protocol. The only one of those we currently wish to support is 64-bit x86.
# Adding further platforms will require adding appropriate relocation code.
ExclusiveArch: x86_64 aarch64

%define debug_package \
%ifnarch noarch\
%global __debug_package 1\
%package -n mokutil-debuginfo\
Summary: Debug information for package %{name}\
Group: Development/Debug\
AutoReqProv: 0\
%description -n mokutil-debuginfo\
This package provides debug information for package %{name}.\
Debug information is useful when developing applications that use this\
package or when debugging this package.\
%files -n mokutil-debuginfo -f debugfiles.list\
%defattr(-,root,root)\
%endif\
%{nil}

# Figure out the right file path to use
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%define ca_signed_arches x86_64
%define rh_signed_arches x86_64 aarch64

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%package -n shim-%{efiarchlc}
Summary: First-stage UEFI bootloader
Requires: mokutil = %{version}-%{release}
Provides: shim = %{version}-%{release}
Obsoletes: shim
# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
Provides: bundled(openssl) = 0.9.8zb

%description -n shim-%{efiarchlc}
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%ifarch x86_64
%package -n shim-ia32
Summary: First-stage UEFI bootloader
Requires: mokutil = %{version}-%{release}
# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
Provides: bundled(openssl) = 0.9.8zb

%description -n shim-ia32
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.
%endif

%package -n mokutil
Summary: Utilities for managing Secure Boot/MoK keys.

%description -n mokutil
Utilities for managing the "Machine's Own Keys" list.

%prep
%setup -T -q -a 0 -n shim-signed-%{version} -c
git init
git config user.email "example@example.com"
git config user.name "rpmbuild -bp"
git add .
git commit -a -q -m "%{version} baseline."
cd mokutil-%{mokutil_version}
git am --ignore-whitespace --directory=mokutil-%{mokutil_version} %{patches} </dev/null
git config --unset user.email
git config --unset user.name
cd ..

%build
%define vendor_token_str %{expand:%%{nil}%%{?vendor_token_name:-t "%{vendor_token_name}"}}
%define vendor_cert_str %{expand:%%{!?vendor_cert_nickname:-c "Red Hat Test Certificate"}%%{?vendor_cert_nickname:-c "%%{vendor_cert_nickname}"}}

%ifarch %{ca_signed_arches}
pesign -i %{shimsrc} -h -P > shim%{efiarchlc}.hash
if ! cmp shim%{efiarchlc}.hash %{unsigned_dir}shim%{efiarchlc}.hash ; then
	echo Invalid signature\! > /dev/stderr
	echo saved hash is $(cat %{unsigned_dir}shim%{efiarchlc}.hash) > /dev/stderr
	echo shim%{efiarchlc}.efi hash is $(cat shim%{efiarchlc}.hash) > /dev/stderr
	exit 1
fi
cp %{shimsrc} shim%{efiarchlc}.efi
%ifarch x86_64
pesign -i %{shimsrcia32} -h -P > shimia32.hash
if ! cmp shimia32.hash %{unsigned_dir_ia32}shimia32.hash ; then
	echo Invalid signature\! > /dev/stderr
	echo saved hash is $(cat %{unsigned_dir_ia32}shimia32.hash) > /dev/stderr
	echo shimia32.efi hash is $(cat shimia32.hash) > /dev/stderr
	exit 1
fi
cp %{shimsrcia32} shimia32.efi
%endif
%endif
%ifarch %{rh_signed_arches}
%pesign -s -i %{unsigned_dir}shim%{efiarchlc}.efi -a %{SOURCE1} -c %{SOURCE1}  -o shim%{efiarchlc}-%{efidir}.efi
%ifarch x86_64
%pesign -s -i %{unsigned_dir_ia32}shimia32.efi -a %{SOURCE1} -c %{SOURCE1}  -o shimia32-%{efidir}.efi
%endif
%endif
%ifarch %{rh_signed_arches}
%ifnarch %{ca_signed_arches}
cp shim%{efiarchlc}-%{efidir}.efi shim%{efiarchlc}.efi
%endif
%endif

%pesign -s -i %{unsigned_dir}mm%{efiarchlc}.efi -o mm%{efiarchlc}.efi -a %{SOURCE1} -c %{SOURCE1}
%pesign -s -i %{unsigned_dir}fb%{efiarchlc}.efi -o fb%{efiarchlc}.efi -a %{SOURCE1} -c %{SOURCE1}

%ifarch x86_64
%pesign -s -i %{unsigned_dir_ia32}mmia32.efi -o mmia32.efi -a %{SOURCE1} -c %{SOURCE1} 
%pesign -s -i %{unsigned_dir_ia32}fbia32.efi -o fbia32.efi -a %{SOURCE1} -c %{SOURCE1} 
%endif

cd mokutil-%{mokutil_version}
./autogen.sh
%configure
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
install -m 0644 shim%{efiarchlc}.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim%{efiarchlc}.efi
install -m 0644 shim%{efiarchlc}-%{efidir}.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim%{efiarchlc}-%{efidir}.efi
install -m 0644 mm%{efiarchlc}.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/mm%{efiarchlc}.efi
install -m 0644 %{bootsrc} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT%{efiarch}.CSV

install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/
install -m 0644 shim%{efiarchlc}.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/BOOT%{efiarch}.EFI
install -m 0644 fb%{efiarchlc}.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/fb%{efiarchlc}.efi

%ifarch aarch64
# In case old boot entries aren't updated
install -m 0644 %{shimsrc} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim.efi
%endif

%ifarch x86_64
# In case old boot entries aren't updated
install -m 0644 shimx64.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim.efi
install -m 0644 %{bootsrc} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT.CSV

install -m 0644 shimia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shimia32.efi
install -m 0644 shimia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shimia32.efi
install -m 0644 shimia32-%{efidir}.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shimia32-%{efidir}.efi
install -m 0644 mmia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/mmia32.efi
install -m 0644 %{bootsrcia32} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOTIA32.CSV

install -m 0644 shimia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/BOOTIA32.EFI
install -m 0644 fbia32.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/fbia32.efi
%endif

cd mokutil-%{mokutil_version}
make PREFIX=%{_prefix} LIBDIR=%{_libdir} DESTDIR=%{buildroot} install

%files -n shim-%{efiarchlc}
/boot/efi/EFI/%{efidir}/shim%{efiarchlc}.efi
/boot/efi/EFI/%{efidir}/shim%{efiarchlc}-%{efidir}.efi
/boot/efi/EFI/%{efidir}/mm%{efiarchlc}.efi
/boot/efi/EFI/%{efidir}/BOOT%{efiarch}.CSV
/boot/efi/EFI/BOOT/BOOT%{efiarch}.EFI
/boot/efi/EFI/BOOT/fb%{efiarchlc}.efi
/boot/efi/EFI/%{efidir}/shim.efi

%ifarch x86_64
/boot/efi/EFI/%{efidir}/BOOT.CSV

%files -n shim-ia32
/boot/efi/EFI/%{efidir}/shimia32.efi
/boot/efi/EFI/%{efidir}/shimia32-%{efidir}.efi
/boot/efi/EFI/%{efidir}/mmia32.efi
/boot/efi/EFI/%{efidir}/BOOTIA32.CSV
/boot/efi/EFI/BOOT/BOOTIA32.EFI
/boot/efi/EFI/BOOT/fbia32.efi
%endif

%files -n mokutil
%{!?_licensedir:%global license %%doc}
%license mokutil-%{mokutil_version}/COPYING
%doc mokutil-%{mokutil_version}/README
%{_bindir}/mokutil
%{_mandir}/man1/*
%{_datadir}/bash-completion/completions/mokutil

%changelog
* Thu Aug 31 2017 Karanbir Singh <kbsingh@centos.org> - 12-1.el7.centos
- interim build

* Mon May 01 2017 Peter Jones <pjones@redhat.com> - 12-1
- Update to 12-1 to work around a signtool.exe bug
  Resolves: rhbz#1445393

* Mon Apr 24 2017 Peter Jones <pjones@redhat.com> - 11-4
- Another shot at better obsoletes.
  Related: rhbz#1310764

* Mon Apr 24 2017 Peter Jones <pjones@redhat.com> - 11-3
- Fix Obsoletes
  Related: rhbz#1310764

* Thu Apr 13 2017 Peter Jones <pjones@redhat.com> - 11-2
- Make sure Aarch64 still has shim.efi as well
  Related: rhbz#1310766

* Wed Apr 12 2017 Peter Jones <pjones@redhat.com> - 11-1
- Rebuild with signed shim
  Related: rhbz#1310766

* Mon Apr 03 2017 Peter Jones <pjones@redhat.com> - 11-0.1
- Update to 11-0.1 to match shim-11-1
  Related: rhbz#1310766
- Fix regression in PE loader
  Related: rhbz#1310766
- Fix case where BDS invokes us wrong and we exec shim again as a result
  Related: rhbz#1310766

* Mon Mar 27 2017 Peter Jones <pjones@redhat.com> - 10-0.1
- Support ia32
  Resolves: rhbz#1310766
- Handle various different load option implementation differences
- TPM 1 and TPM 2 support.
- Update to OpenSSL 1.0.2k

* Mon Jul 20 2015 Peter Jones <pjones@redhat.com> - 0.9-2
- Apparently I'm *never* going to learn to build this in the right target
  the first time through.
  Related: rhbz#1100048

* Mon Jun 29 2015 Peter Jones <pjones@redhat.com> - 0.9-0.1
- Bump version for 0.9
  Also use mokutil-0.3.0
  Related: rhbz#1100048

* Tue Jun 23 2015 Peter Jones <pjones@redhat.com> - 0.7-14.1
- Fix mokutil_version usage.
  Related: rhbz#1100048

* Mon Jun 22 2015 Peter Jones <pjones@redhat.com> - 0.7-14
- Pull in aarch64 build so they can compose that tree.
  (-14 to match -unsigned)
  Related: rhbz#1100048

* Wed Feb 25 2015 Peter Jones <pjones@redhat.com> - 0.7-12
- Fix some minor build bugs on Aarch64
  Related: rhbz#1190191

* Tue Feb 24 2015 Peter Jones <pjones@redhat.com> - 0.7-11
- Fix section loading on Aarch64
  Related: rhbz#1190191

* Wed Dec 17 2014 Peter Jones <pjones@redhat.com> - 0.7-10
- Rebuild for Aarch64 to get \EFI\BOOT\BOOTAA64.EFI named right.
  (I managed to fix the inputs but not the outputs in -9.)
  Related: rhbz#1100048

* Wed Dec 17 2014 Peter Jones <pjones@redhat.com> - 0.7-9
- Rebuild for Aarch64 to get \EFI\BOOT\BOOTAA64.EFI named right.
  Related: rhbz#1100048

* Tue Oct 21 2014 Peter Jones <pjones@redhat.com> - 0.7-8
- Build for aarch64 as well 
  Related: rhbz#1100048
- out-of-bounds memory read flaw in DHCPv6 packet processing
  Resolves: CVE-2014-3675
- heap-based buffer overflow flaw in IPv6 address parsing
  Resolves: CVE-2014-3676
- memory corruption flaw when processing Machine Owner Keys (MOKs)
  Resolves: CVE-2014-3677

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 0.7-7
- Make sure we use the right keys on Aarch64.
  (It's only a demo at this stage.)
  Related: rhbz#1100048

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 0.7-6
- Add ARM Aarch64.
  Related: rhbz#1100048

* Thu Feb 27 2014 Peter Jones <pjones@redhat.com> - 0.7-5.2
- Get the right signatures on shim-redhat.efi
  Related: rhbz#1064449

* Thu Feb 27 2014 Peter Jones <pjones@redhat.com> - 0.7-5.1
- Update for signed shim for RHEL 7
  Resolves: rhbz#1064449

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-5
- Fix shim-unsigned deps.
  Related: rhbz#1032583

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-4
- Make dhcp4 work better.
  Related: rhbz#1032583

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 0.7-3
- Make lockdown include UEFI and other KEK/DB entries.
  Related: rhbz#1030492

* Fri Nov 08 2013 Peter Jones <pjones@redhat.com> - 0.7-2
- Handle SetupMode better in lockdown as well
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.7-1
- Don't treat SetupMode variable's presence as meaning we're in SetupMode.
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.6-3
- Use the correct CA and signer certificates.
  Related: rhbz#996863

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 0.6-1
- Update to 0.6-1
  Resolves: rhbz#1008379

* Wed Aug 07 2013 Peter Jones <pjones@redhat.com> - 0.4-3.2
- Depend on newer pesign.
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3.1
- Rebuild with newer pesign
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3
- Update for RHEL signing with early test keys.
  Related: rhbz#989442

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 0.4-1
- Provide a fallback for uninitialized Boot#### and BootOrder
  Resolves: rhbz#963359
- Move all signing from shim-unsigned to here
- properly compare our generated hash from shim-unsigned with the hash of
  the signed binary (as opposed to doing it manually)

* Fri May 31 2013 Peter Jones <pjones@redhat.com> - 0.2-4.4
- Re-sign to get alignments that match the new specification.
  Resolves: rhbz#963361

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2-4.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jan 02 2013 Peter Jones <pjones@redhat.com> - 0.2-3.3
- Add obsoletes and provides for earlier shim-signed packages, to cover
  the package update cases where previous versions were installed.
  Related: rhbz#888026

* Mon Dec 17 2012 Peter Jones <pjones@redhat.com> - 0.2-3.2
- Make the shim-unsigned dep be on the subpackage.

* Sun Dec 16 2012 Peter Jones <pjones@redhat.com> - 0.2-3.1
- Rebuild to provide "shim" package directly instead of just as a Provides:

* Sat Dec 15 2012 Peter Jones <pjones@redhat.com> - 0.2-3
- Also provide shim-fedora.efi, signed only by the fedora signer.
- Fix the fedora signature on the result to actually be correct.
- Update for shim-unsigned 0.2-3

* Mon Dec 03 2012 Peter Jones <pjones@redhat.com> - 0.2-2
- Initial build
