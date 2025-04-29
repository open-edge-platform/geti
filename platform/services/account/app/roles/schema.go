// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

const spicedbSchema = `
	definition user {
      /** Service accounts linked to the user */
      relation service_accounts: service_account
    }
    
    definition service_account {
      /** This type represents service accounts (e.g. Personal Access Tokens) */
    }

    definition organization {
    /** Organization admin users */
    relation organization_admin: user
    /** Organization contributors */
    relation organization_contributor: user

    /** Permission to manage organization */
    permission can_manage = organization_admin

    /** Permission to contribute to organization */
    permission can_contribute = organization_contributor +
                                organization_contributor->service_accounts +
                                organization_admin->service_accounts +
                                can_manage
    }
    
    definition workspace {
      /** Workspace admin users */
      relation workspace_admin: user
      /** Workspace contributor (non-admin) users */
      relation workspace_contributor: user
      /** Parent organization of the workspace */
      relation parent_organization: organization
    
      /** Permission to manage workspace */
      permission can_manage = workspace_admin +
                              workspace_admin->service_accounts +
                              parent_organization->can_manage
      /** Permission to contribute to the workspace, granted to workspace contributors, administrators and their service accounts */
      permission can_contribute = workspace_contributor +
                                  workspace_contributor->service_accounts +
                                  can_manage
      /** Permission to view all workspace jobs, granted to administrators and their service accounts */
      permission view_all_workspace_jobs = can_manage + workspace_admin->service_accounts
      permission view_workspace = can_contribute
      permission edit_workspace = can_manage
      permission delete_workspace = can_manage
      permission create_new_project = can_contribute
    }
    
    definition project {
      /** Project manager users */
      relation project_manager: user
      /** Project contributor users */
      relation project_contributor: user
      /** Parent workspace of the project */
      relation parent_workspace: workspace
    
      /** Permission to manage project, granted to project managers and parent workspace admins */
      permission can_manage = project_manager +
                              project_manager->service_accounts +
                              parent_workspace->can_manage
      /** Permission to contribute to the project, granted to project contributors, project managers and their service accounts */
      permission can_contribute = project_contributor +
                                  project_contributor->service_accounts +
                                  project_manager->service_accounts +
                                  can_manage
      permission view_project = can_contribute
      permission edit_project = can_manage
      permission delete_project = can_manage
    }

    definition job {
      /** Parent entity: workspace for workspace scoped jobs, project for project scoped ones */      
      relation parent_entity: workspace | project    
      /** Users with either view_workspace or view_project permission can view jobs on the platform */
      permission view_job = parent_entity->view_project + parent_entity->view_workspace
    }
`
