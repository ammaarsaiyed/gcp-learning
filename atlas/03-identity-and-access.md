# 03 · Identity and access

Every request in GCP is evaluated as: *who* is calling (authentication) → *are they allowed* (authorization) → from *where and under what conditions* (context). In a bank this domain decides most audit findings.

---

### Authentication vs authorization
`core` · Related: IAM, OAuth 2.0, OpenID Connect
**What:** **Authentication (authn)** proves *who you are*: passwords, keys, certificates, tokens, MFA. **Authorization (authz)** decides *what you may do*: roles, policies, ACLs.
**How:** Typically: authenticate once → receive a token → present the token on each call → the resource server checks the token, then checks policy.
**GCP:** Google identities authenticate through Google Sign-In or a federated IdP. Workloads authenticate with service account credentials. **IAM** handles authorization.
**Watch out:** HTTP **401** means "not authenticated" (missing or bad credentials). **403** means "authenticated but not allowed".

### Identity provider (IdP) and single sign-on (SSO)
`core` · Related: SAML 2.0, OpenID Connect, Cloud Identity
**What:** An **IdP** is the system of record that authenticates users (Microsoft Entra ID, Okta, Ping, Google). **SSO** lets users sign in once at the IdP and access many apps that trust it.
**GCP:** Banks usually keep Entra ID or Okta as the IdP. **Cloud Identity** holds the Google-side user and group objects (synced with **Google Cloud Directory Sync**, GCDS, or SCIM provisioning), and sign-in is federated back to the corporate IdP through SAML or OIDC. **Workforce Identity Federation** can skip the Google user objects altogether.

### SAML 2.0
`working` · Related: IdP and SSO, OpenID Connect
**What:** An XML-based standard for enterprise SSO. The IdP sends a signed **assertion** about the user to the **service provider (SP)**, usually through the browser.
**How:** The user hits the SP → is redirected to the IdP → authenticates → the IdP posts a signed SAML response back → the SP validates the signature and creates a session.
**GCP:** Used for SSO from corporate IdPs into Cloud Identity / Workspace, and as one option for Workforce Identity Federation.

### OAuth 2.0
`core` · Related: OpenID Connect, Access tokens, Service accounts, Apigee
**What:** A framework for **delegated authorization**: a *client* app gets an **access token** to call a *resource server* on behalf of a *resource owner* (a user) or as itself, without handling the user's password.
**How:** Roles: resource owner, client, **authorization server** (issues tokens), resource server (the API). Grant types (flows): **authorization code + PKCE** (user-facing apps; the user consents in the browser and the client exchanges a short-lived code for tokens), **client credentials** (machine-to-machine, no user), **device code** (TVs and CLIs), plus **refresh tokens** for new access tokens without re-prompting. Tokens carry **scopes** (permission categories).
**GCP:** Google APIs accept OAuth 2.0 access tokens. Service accounts effectively use a client-credentials-style flow (signed JWT assertion → access token). Apigee acts as an OAuth authorization server for your own APIs. **FAPI** (the Financial-grade API profile) hardens OAuth for Open Banking.
**Watch out:** OAuth is *authorization*. Signing in users is OIDC, which is built on top of it.

### OpenID Connect (OIDC)
`core` · Related: OAuth 2.0, JWT, ID token
**What:** An identity layer on top of OAuth 2.0 that tells the client *who the user is*, through an **ID token** (a JWT).
**How:** Same flows as OAuth, with the `openid` scope. The ID token holds claims like `sub` (subject id), `email`, `iss` (issuer), `aud` (the intended client), `exp`. Discovery documents (`/.well-known/openid-configuration`) and **JWKS** endpoints publish the signing keys.
**GCP:** Google issues OIDC ID tokens to service accounts and users. Cloud Run, Cloud Run functions and IAP verify them. Workload Identity Federation accepts OIDC tokens from external IdPs (GitHub Actions, Azure, Kubernetes, GitLab).

### JWT (JSON Web Token)
`core` · Related: OpenID Connect, OAuth 2.0, IAP
**What:** A compact token format: `base64url(header).base64url(payload).signature`. The payload holds **claims** (`iss`, `sub`, `aud`, `exp`, `iat`, plus custom claims).
**How:** It's **signed, not encrypted** by default: anyone can read the claims, but nobody can change them without breaking the signature. Verifiers check the signature with the issuer's public key (from JWKS), then check `exp`, `iss`, and that **`aud` matches themselves**.
**GCP:** IAP adds a signed JWT header (`x-goog-iap-jwt-assertion`) that backends should verify. Cloud Run ID tokens are JWTs with `aud` = the service URL.
**Watch out:** Skipping the `aud` check lets a token minted for service A be replayed against service B. Never put secrets in a JWT payload.

### Access tokens, ID tokens and refresh tokens
`core` · Related: OAuth 2.0, OpenID Connect, Service account impersonation
**What:** An **access token** authorizes calls to an API (for Google APIs it's usually opaque and lasts about 1 hour). An **ID token** asserts identity to a specific audience (a JWT). A **refresh token** is a long-lived credential used to get new access tokens.
**GCP:** You call Google APIs (Storage, BigQuery, Gemini) with an **access token** (`gcloud auth print-access-token`). You call **private Cloud Run services or IAP-protected apps** with an **ID token** whose audience is that service (`gcloud auth print-identity-token --audiences=URL`).
**Watch out:** Using the wrong token type for the target is the classic cause of "401 from my Cloud Run service".

### API keys
`working` · Related: OAuth 2.0, Apigee
**What:** A simple string that identifies a *project or app*, not a principal. Used for quota and billing attribution on some Google APIs (Maps, some AI APIs through AI Studio).
**GCP:** Restrict keys by API and by caller (IP, referrer, app). Many enterprise APIs don't accept API keys at all, because they need IAM. In Apigee, API keys identify consumer apps, often combined with OAuth.
**Watch out:** An API key isn't strong authentication. Leaked keys are a common incident. Prefer IAM-based authentication.

### Multi-factor authentication (MFA / 2-Step Verification)
`working` · Related: IdP and SSO, Zero trust
**What:** Requiring two or more factors: something you know, have, or are. **Phishing-resistant** MFA (FIDO2 / WebAuthn security keys, passkeys) beats SMS and one-time codes.
**GCP:** Enforced through Cloud Identity 2SV or the federated IdP. Banks require MFA for all console and CLI access, and hardware keys for super admins and privileged roles.

### Cloud Identity, Google Workspace and super admins
`core` · Related: IdP and SSO, Organization
**What:** **Cloud Identity** is Google's identity-as-a-service (users, groups, devices) without Workspace apps. Your GCP **Organization** resource is tied to a Cloud Identity or Workspace domain.
**How:** Users and groups are created manually, synced from AD/LDAP with **GCDS**, or provisioned through SCIM from Entra ID or Okta. **Super administrators** control the domain itself and can grant themselves anything in GCP.
**Watch out:** Keep a small number of super admins, with hardware MFA and no day-to-day use, and use separate break-glass accounts.

### Workforce Identity Federation
`working` · Related: IdP and SSO, Workload Identity Federation
**What:** Lets *human users* from an external IdP (Entra ID, Okta, any OIDC or SAML IdP) access the GCP console and APIs **without** Google accounts in Cloud Identity.
**How:** You configure a workforce pool and provider. IdP attributes (groups, department) map to Google attributes. IAM grants use `principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/group/GROUP`.
**Watch out:** Not every Google Cloud product supports workforce identities. Check before you choose it over synced Cloud Identity.

### Principals
`core` · Related: IAM roles, Service accounts, Groups
**What:** The "who" in an IAM binding: `user:` (Google account), `group:` (Google group, **preferred**), `serviceAccount:`, `domain:` (everyone in a Cloud Identity / Workspace domain), `principal://` and `principalSet://` (federated identities from workforce or workload pools), `allAuthenticatedUsers` (any Google account, which is almost always wrong), and `allUsers` (anyone, so public).
**GCP:** The org policy **Domain Restricted Sharing** (`iam.allowedPolicyMemberDomains`) blocks granting access to identities outside your domains, including `allUsers`. Banks enforce it, with narrow exceptions.

### IAM roles: basic, predefined and custom
`core` · Related: Principals, IAM policy inheritance, Least privilege
**What:** A role is a collection of **permissions** (`service.resource.verb`, for example `bigquery.tables.getData`). **Basic roles** (Owner, Editor, Viewer) are broad and pre-date IAM, so avoid them in production. **Predefined roles** are curated per service by Google (`roles/storage.objectViewer`, `roles/aiplatform.user`). **Custom roles** are your own bundles, at org or project level, and you maintain them as services add permissions.
**How:** Permissions are fine-grained. Roles are what you grant. You can't grant a permission directly.
**Watch out:** Editor has thousands of permissions, so "Editor on the project" fails every least-privilege review.

### IAM policies and inheritance
`core` · Related: Resource hierarchy, IAM deny policies, Organization Policy
**What:** An **allow policy** is attached to a resource (org, folder, project, or individual resource such as a bucket, topic, secret or BigQuery dataset) and holds **bindings**: role → list of principals, with an optional condition.
**How:** Effective access on a resource = the union of its own policy and every ancestor's. **Allow policies can only add.** You can't remove inherited access lower down; you'd need a **deny policy** or to remove it at the source. Policies are versioned and use etags for safe concurrent edits.
**Watch out:** Granting at the org or folder level is powerful and dangerous. A single folder-level BigQuery Admin grant covers hundreds of projects.

### IAM Conditions
`working` · Related: IAM policies, Secure Tags, Privileged Access Manager
**What:** **CEL** expressions attached to a binding that must evaluate to true for the grant to apply.
**How:** They can match on request time (temporary access, business hours), resource name or type (only buckets starting with `prj-ml-`), resource **tags** (only resources tagged `env=dev`), and some request attributes.
**GCP:** "Give the contractor access until Friday" and "this team can only act on resources tagged with their cost centre" are condition use cases. Not every service and role supports conditions.

### IAM deny policies
`working` · Related: IAM policies, Organization Policy
**What:** Policies that explicitly **deny** specific permissions to principals, evaluated **before** allow policies. A deny always wins.
**How:** Attached at org, folder or project level, with exception principals (for example "deny `iam.serviceAccountKeys.create` to everyone except the security group").
**GCP:** Used for hard guardrails that no amount of allow grants can override.

### Principal access boundary (PAB)
`aware` · Related: IAM deny policies, VPC Service Controls
**What:** Policies that limit *which resources* a principal is eligible to access at all (for example "these identities can only ever access resources in our organization"), whatever allow policies elsewhere say. A defence against cross-org data access.

### Service accounts
`core` · Related: Application Default Credentials, Service account impersonation, Workload Identity Federation
**What:** Non-human identities for workloads (`name@project.iam.gserviceaccount.com`). A service account is both a **principal** (it can be granted roles) and a **resource** (people can be granted the right to *use* or *impersonate* it).
**How:** Kinds: **user-managed** (you create them, one per workload), **default service accounts** (Compute Engine's `PROJECT_NUMBER-compute@…`, App Engine's), and **service agents** (Google-managed identities that services use to act in your project, `service-PROJECT_NUMBER@gcp-sa-SERVICE.iam.gserviceaccount.com`). You *attach* a service account to a VM, Cloud Run service, GKE workload or Cloud Build job. Deploying with a service account requires `iam.serviceAccountUser` on it, which is what stops privilege escalation.
**Watch out:** Default service accounts often have Editor. Banks disable automatic grants (`iam.automaticIamGrantsForDefaultServiceAccounts`) and require a dedicated, least-privilege service account per workload.

### Service account keys
`core` · Related: Service accounts, Workload Identity Federation, Organization Policy
**What:** Downloadable JSON private keys that let anything, anywhere, act as the service account until the key is revoked.
**How:** They're long-lived (no expiry by default), easily copied into git, laptops and CI variables, and hard to audit.
**GCP:** Banks enforce the `iam.disableServiceAccountKeyCreation` and `iam.disableServiceAccountKeyUpload` org policies. The replacements are: attached service accounts (GCP workloads), **Workload Identity Federation** (external workloads) and **impersonation** (humans).

### Application Default Credentials (ADC)
`core` · Related: Service accounts, Metadata server, Client libraries
**What:** The lookup strategy Google client libraries use to find credentials automatically, so code never contains them.
**How:** In order: (1) the `GOOGLE_APPLICATION_CREDENTIALS` env var (a credential file: a key, an external-account config for WIF, or impersonation config); (2) the user's ADC file from `gcloud auth application-default login`; (3) the **metadata server** of the environment (the attached service account on GCE, GKE, Cloud Run and so on).
**GCP:** The same code runs on your laptop (your user credentials) and in Cloud Run (its service account) without changes.

### Metadata server
`working` · Related: Application Default Credentials, Service accounts
**What:** An internal endpoint (`metadata.google.internal` / `169.254.169.254`) available to every VM, GKE node or Pod and serverless instance. It serves instance metadata and **short-lived access and ID tokens** for the attached service account.
**How:** Requests must include the header `Metadata-Flavor: Google`, which is a defence against some SSRF attacks.
**Watch out:** **SSRF** (server-side request forgery) bugs that let an attacker make the app fetch arbitrary URLs can leak tokens from the metadata server. Least-privilege service accounts limit the damage.

### Service account impersonation and short-lived credentials
`core` · Related: Service accounts, Privileged Access Manager, Separation of duties
**What:** A principal with `roles/iam.serviceAccountTokenCreator` on a service account can mint **short-lived** access tokens, ID tokens or signed JWTs *as* that service account, through the **IAM Service Account Credentials API**. No key needed.
**How:** `gcloud … --impersonate-service-account=SA`, or Terraform's `impersonate_service_account`. Tokens expire (about 1 hour by default). Audit logs record both the caller and the impersonated service account.
**GCP:** The standard pattern: humans hold almost no direct roles, and impersonate a deployment service account for privileged actions. That gives traceability and an easy revocation point.

### Workload Identity Federation
`core` · Related: Service account keys, OpenID Connect, Security Token Service
**What:** Lets workloads *outside* Google Cloud (GitHub Actions, GitLab, Azure, AWS, on-prem Kubernetes, any OIDC or SAML IdP) access GCP **without service account keys**.
**How:** The external workload gets a token from its own IdP (for example GitHub's OIDC token for a workflow run) → Google's **Security Token Service** exchanges it for a federated token, checking the **workload identity pool / provider** configuration, its attribute mappings and its **attribute conditions** (for example `assertion.repository == 'bank/payments-api'`) → it optionally impersonates a service account, or uses direct resource access → calls the Google APIs.
**Watch out:** Attribute conditions are the security boundary. A pool that trusts "any GitHub repo" means anyone on GitHub. Always restrict to your org, repo and branch.

### Workload Identity Federation for GKE
`core` · Related: Workload Identity Federation, Kubernetes service accounts
**What:** Maps a **Kubernetes service account** (namespace/name) to an IAM principal, so Pods get Google credentials from the GKE metadata server without keys.
**How:** You grant IAM roles directly to `principal://…/subject/ns/NAMESPACE/sa/KSA`, or bind the Kubernetes service account to impersonate a Google service account. Each workload gets its own identity instead of sharing the node's service account.

### Identity-Aware Proxy (IAP)
`core` · Related: Zero trust, Context-aware access, JWT
**What:** A Google-managed reverse proxy that authenticates users and checks IAM **before** a request reaches your app (HTTPS) or VM (TCP).
**How:** **IAP for web apps** works on Application Load Balancer backends, App Engine and Cloud Run: users sign in with Google or a federated identity, IAP checks `roles/iap.httpsResourceAccessor` plus context-aware access levels, then forwards the request with a signed JWT header. **IAP TCP forwarding** handles SSH, RDP and other TCP to VMs without public IPs or bastions (firewall source `35.235.240.0/20`).
**GCP:** It's the fastest way to put an internal tool (for example an internal GenAI app for staff) behind corporate identity with no VPN. The backend should still verify the IAP JWT.

### Zero trust and BeyondCorp
`core` · Related: IAP, Context-aware access, mTLS
**What:** A security model where **network location grants no trust**. Every request is authenticated, authorized and evaluated in context (user, device state, location, risk), at every hop.
**How:** It replaces "on the corporate network = trusted" with per-request identity-aware access, strong device identity, mTLS between services and least privilege. **BeyondCorp** is Google's internal implementation. **Chrome Enterprise Premium** (formerly BeyondCorp Enterprise) is the product.
**GCP:** IAP + Access Context Manager (users), service mesh mTLS + authorization policies (services), VPC-SC (data access), short-lived credentials.

### Access Context Manager and access levels
`working` · Related: VPC Service Controls, Context-aware access, IAP
**What:** Defines **access levels**: named conditions on request context such as source IP ranges, device policy (corporate-managed, encrypted, OS version; needs endpoint verification), geography and identity.
**GCP:** Access levels are used by **VPC Service Controls** (allowing access into a perimeter from approved contexts) and by **IAP / context-aware access** (allowing an app only from managed devices).

### Context-aware access
`working` · Related: IAP, Access Context Manager, Zero trust
**What:** Applying access levels to user access to the Google Cloud console and APIs, IAP-protected apps and Workspace, for example "the console only from bank-managed devices on the corporate network".

### Privileged Access Manager (PAM)
`working` · Related: Least privilege, IAM Conditions, Break-glass access
**What:** **Just-in-time (JIT)**, time-bound privilege elevation. Users request an *entitlement* (a set of roles on a resource), optionally with justification and approval, and the grant expires automatically.
**GCP:** It replaces standing admin access ("Owner forever") with "Owner for 2 hours after approval, fully audited". It's a strong control for production access in regulated firms.

### Least privilege, separation of duties and break-glass access
`core` · Related: IAM roles, Privileged Access Manager, Policy Intelligence
**What:** **Least privilege:** grant only the permissions needed, at the narrowest scope, for the shortest time. **Separation of duties (SoD):** no single person can complete a sensitive action end to end (for example the developer who writes code can't approve its prod deployment; the key admin can't read the data the key protects). **Break-glass:** emergency high-privilege access that is tightly controlled, alerted on and reviewed.
**GCP:** Separate the *KMS admin* and *KMS encrypter/decrypter* roles, separate the *network admin* (host project) from *app deployers* (service projects), require deployments through a pipeline service account, keep break-glass accounts with hardware keys and alert on every use through log-based alerts.

### Policy Intelligence (Recommender, Analyzer, Troubleshooter)
`working` · Related: Least privilege, IAM policies
**What:** Tools to understand and shrink access. The **IAM role recommender** suggests removing permissions unused for 90 days. **Policy Analyzer** answers "who can access this resource?" and "what can this principal access?". **Policy Troubleshooter** explains why a specific access attempt was allowed or denied (allow, deny and PAB policies, conditions).

### RBAC vs ABAC
`working` · Related: IAM roles, IAM Conditions
**What:** **Role-based access control** grants permissions through roles assigned to identities. **Attribute-based access control** decides from attributes of the user, the resource and the context.
**GCP:** IAM is mainly RBAC, with ABAC added through **IAM Conditions** and **tags**. Kubernetes has its own RBAC (Roles and RoleBindings) for in-cluster access, which works alongside IAM.

### OS Login
`working` · Related: IAP, Service accounts
**What:** Manages SSH access to Linux VMs through **IAM** (`roles/compute.osLogin` / `osAdminLogin`) instead of SSH keys in metadata. It supports 2FA and gives audit logs tied to identities.
**GCP:** Often enforced by org policy (`compute.requireOsLogin`). Combined with IAP TCP forwarding: no public IPs, no key sprawl, every session attributable.

### Identity Platform (customer identity)
`working` · Related: OAuth 2.0, OpenID Connect
**What:** Customer identity and access management (CIAM) for *your app's end users*, not employees: sign-up and sign-in, social and enterprise IdPs, MFA, multi-tenancy, built on Firebase Authentication.
**Watch out:** Don't confuse it with Cloud Identity (employees and admins). Large banks usually have their own customer identity stack, but Identity Platform appears in greenfield designs.

### Groups and access reviews
`working` · Related: Principals, Least privilege
**What:** Grant roles to **groups** that map to job functions (`gcp-payments-dev@bank.com`), never to individuals. Then joiners, movers and leavers are handled by the identity team through group membership, and periodic **access reviews** look at groups, not thousands of bindings.
