# Private team publication handoff

## Recommended arrangement

Ask the approved project GitHub organization owner to create one new
**private organization-owned repository** for the code branch and runtime
Release. Use the organization approved to hold this project's data.
The public project remains unchanged. Do not use a public fork,
a personal repository, or an organization-wide internal repository
as a substitute for the private team audience.

Give the approved project team Read access for cloning and downloads.
Grant Write only to developers who need to push and designated release
maintainers. Keep Admin for the organization owners or delegated repository
administrators. Release management is available to Write users, so treat
that role as a publication capability. Keep base organization permissions
as narrow as the owner's policy allows and review outside collaborators.
If working with a private copy of the code history, obtain approval for
that history as well as the new branch. References:

- https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-roles-for-an-organization
- https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository

Teammates sign in with their own account using gh auth login --hostname
github.com --web and complete organization SSO if applicable. gh repo clone
uses that identity for the private checkout and setup uses the same CLI
identity for release downloads. No shared token or credential file is needed.
The clone origin supplies the asset repository by default. Use --asset-repo
only if the organization approves separate code and asset repositories.

- https://cli.github.com/manual/gh_auth_login
- https://docs.github.com/en/authentication/authenticating-with-single-sign-on/about-authentication-with-single-sign-on

## After authorization, for the designated maintainer

1. Obtain the exact private OWNER/REPO, the approved team audience, and
   recorded data-owner clearance for the exact 21 runtime attachments,
   including the two held demo-100 files. Fresh-v4 remains outside the
   runtime release. Stop if any clearance is missing.
2. Confirm PRIVATE in gh repo view OWNER/REPO --json visibility. Confirm
   membership and applicable SSO with the repository owner. Add this
   repository as a separate Git remote and push the reviewed branch there
   only. Set the team's clone instructions to that branch. Keep the existing
   integration/portable-onboarding branch and the public remote untouched.
3. On an authorized machine with a verified source tree matching assets.json,
   run the local attachment preparer:

       python onboarding/prepare_release.py --assets /private/approved-source --output /private/new-release-staging --clearance-reference APPROVAL-ID

   The source layout is relative paths in assets.json. The helper verifies
   every exact size and hash before copying and writes only the named
   release attachments. It checks again after copying. It does not validate
   the approval record independently and has no upload capability.
4. In the private repository, make a draft s2-runtime-v1 release targeting
   the exact reviewed onboarding commit. Attach only the 21 generated
   files. Review repo visibility, membership, tag, files and checksums
   before publishing. Keep the version tag stable and use an immutable
   release if the organization permits. Verify developer Read access by
   running setup from a fresh private clone after approved publication.
   Do not upload a corpus ZIP, any validation set, raw evaluation directories
   or credentials. Delete the temporary local attachment directory using
   the project's handling rules after verification.

No repository, tag, Release or upload was created by this handoff.
