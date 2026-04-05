## Task: ML01 Samba Shares + Skill File Updates

Mode: Code

---

### Objective

Two Samba shares are configured on ML01 exposing `/opt/repos` and `/opt/repos-internal` to the local network, accessible from a Windows desktop using the `crainbramp` user. Additionally, the kc-structured-prompt skill files are updated to reference GLM-5.1 and AGENTS.md instead of GLM-4.7 and memory bank.

---

### Scope

**Modify:**
- Samba configuration (`/etc/samba/smb.conf`)
- Samba user setup for `crainbramp`
- Firewall rules (if UFW is active, open ports 139, 445)
- Skill files (location specified below)

**Reference:**
- Current ML01 network config (10.25.20.0/24 subnet, management at 10.25.10.0/24)

---

### Deliverables & Validation

1. **Samba installed and running**
   - [ ] `samba` package installed (`apt install samba`)
   - [ ] `smbd` service enabled and running (`systemctl enable --now smbd`)
   - [ ] `nmbd` service enabled and running (`systemctl enable --now nmbd`)

2. **Share: `repos` → `/opt/repos`**
   - [ ] Share name: `repos`
   - [ ] Path: `/opt/repos`
   - [ ] Read/write access for `crainbramp`
   - [ ] No guest access
   - [ ] Create mask: 0664, directory mask: 0775
   - [ ] Force user: `crainbramp`, force group: `crainbramp`
   - [ ] From Windows: `\\ml01\repos` or `\\10.25.20.34\repos` mounts and shows contents

3. **Share: `repos-internal` → `/opt/repos-internal`**
   - [ ] Share name: `repos-internal`
   - [ ] Path: `/opt/repos-internal`
   - [ ] Same permissions as `repos` share
   - [ ] From Windows: `\\ml01\repos-internal` mounts and shows contents

4. **Samba user configured**
   - [ ] `crainbramp` added as Samba user (`smbpasswd -a crainbramp`)
   - [ ] Password set (prompt operator to enter password interactively)

5. **Firewall rules (if UFW active)**
   - [ ] Check `ufw status`; if active, allow Samba: `ufw allow samba`
   - [ ] If UFW is inactive, skip — do not enable it

6. **Skill file updates: kc-structured-prompt**

   Locate the skill files. Check these paths in order:
   - `/opt/repos/` or `/opt/repos-internal/` (search for `kc-structured-prompt`)
   - `/home/crainbramp/`
   - If not found, report the search results and skip this deliverable

   Once found, apply these changes:

   **SKILL.md:**
   - [ ] Replace all references to `GLM-4.7` or `GLM 4.7` with `GLM-5.1` or `GLM 5.1`
   - [ ] Replace `.kilocode/memory-bank/` references with `AGENTS.md` in the Quick Reference template
   - [ ] Replace `Context: .kilocode/memory-bank/` with `Context: AGENTS.md at repo root` in the Environment section
   - [ ] Remove the constraint about "Memory bank available at `.kilocode/memory-bank/`" — replace with "Context: `AGENTS.md` at repo root"

   **assets/template.md:**
   - [ ] Replace `- .kilocode/memory-bank/ for project context` with `- AGENTS.md at repo root`
   - [ ] Replace `- Context: .kilocode/memory-bank/` with `- Context: AGENTS.md at repo root`

---

### Constraints

- Do not enable UFW if it is not already active
- Samba shares should only be accessible from the local subnets (10.25.10.0/24 and 10.25.20.0/24) — add `hosts allow = 10.25.10. 10.25.20. 127.` to smb.conf
- Do not modify any files under `/opt/repos/` or `/opt/repos-internal/` other than the skill files specified above
- Use `testparm` to validate smb.conf before restarting services

---

**Environment:**
- ML01 bare metal, Ubuntu 24.04
- User: `crainbramp` (has sudo)
- ML01 IP: check with `hostname -I` (likely 10.25.20.34 or similar on the proj VLAN)
- Run as `crainbramp` with sudo for package install and service management
