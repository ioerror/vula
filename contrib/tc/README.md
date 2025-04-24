# tc based guardrail policy prototypes

The shell scripts `tc-egress-cake.sh`, `tc-egress-htb.sh`,
`tc-ingress-clsact.sh`, `tc-egress-clsact.sh`, `tc-ingress-cake.sh`, and
`tc-ingress-htb.sh` in this directory are included to demonstrate enforcing a
specific policy using the Linux traffic control infrastructure. Unless you are
absolutely certain that you understand the use of these scripts and how to
ensure that they function correctly, do not use these programs. The default
values are not correct and must be changed but we provide sample values to
assist a reader in understanding how it should work.

## No shaper with policy enforcement: clsact

Edit `tc-egress-clsact.sh` and `tc-ingress-clsact.sh` to set the correct values
for each variable and then run the scripts to setup the policy enforcement
including redirection.

## Shaper with policy enforcement: cake

Edit `tc-egress-cake.sh` and `tc-ingress-cake.sh` to set the correct values for
each variable and then run the scripts to setup the policy enforcement
including redirection.

## Shaper with policy enforcement: htb

Edit `tc-egress-htb.sh` and `tc-ingress-htb.sh` to set the correct values for
each variable and then run the scripts to setup the policy enforcement
including redirection.
