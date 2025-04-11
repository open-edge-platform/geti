// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package main

import (
	"context"
	"flag"
	"log"
	"time"

	"geti.com/account_service_grpc/pb"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	flag.Parse()
	// Set up a connection to the server.
	conn, e := grpc.Dial("localhost:5001", grpc.WithTransportCredentials(insecure.NewCredentials())) //nolint:all (SA1019: deprecated)
	if e != nil {
		log.Fatalf("did not connect: %v", e)
	}
	defer func(conn *grpc.ClientConn) {
		err := conn.Close()
		if err != nil {
			log.Printf("An error ocurred while closing the connection: %v", err)
		}
	}(conn)

	orgClient := pb.NewOrganizationClient(conn)

	// Contact the server and print out its response.
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	fakeOrgData := pb.OrganizationData{
		Name:     "ACME",
		Country:  "BGD",
		Location: "Dhaka",
		Type:     "B2C",
		CellId:   "1a234b",
		Status:   "ACT",
	}

	r, e := orgClient.Create(ctx, &fakeOrgData)
	if e != nil {
		log.Fatalf("could not create organization: %v", e)
	}
	log.Printf("Name: %s", r.GetName())
	log.Printf("ID: %s", r.GetId())

	workspaceClient := pb.NewWorkspaceClient(conn)

	fakeWorkspaceData := pb.WorkspaceData{
		Name:           "fake-workspace",
		OrganizationId: r.GetId(),
	}

	workspaceResponse, e := workspaceClient.Create(ctx, &fakeWorkspaceData)
	if e != nil {
		log.Fatalf("could not create workspace: %v", e)
	}
	log.Printf("Name: %s", workspaceResponse.GetName())
	log.Printf("ID: %s", workspaceResponse.GetId())

	fakeModifiedOrgData := pb.OrganizationData{
		Id:       r.GetId(),
		Name:     "Umbrella",
		Country:  "SWE",
		Location: "Stockholm",
		Type:     "B2B",
		CellId:   "5fa21",
		Status:   "SSP",
	}

	orgData, e := orgClient.Modify(ctx, &fakeModifiedOrgData)
	if e != nil {
		log.Fatalf("could not modify organization: %v", e)
	}

	log.Printf("Name: %s", orgData.GetName())

	idRequest := pb.OrganizationIdRequest{Id: r.GetId()}
	orgDataWithAdmins, e := orgClient.GetById(ctx, &idRequest)
	if e != nil {
		log.Fatalf("could not get organization: %v", e)
	}

	log.Printf("Name: %s", orgDataWithAdmins.GetName())

	findReq := pb.FindOrganizationRequest{
		Country: "BGD",
		Status:  "ACT",
		Limit:   3,
		Skip:    2,
	}

	response, e := orgClient.Find(ctx, &findReq)
	if e != nil {
		log.Fatalf("could not find organization: %v", e)
	}
	log.Printf("count: %v", response.TotalCount)

	wkscpFindReq := pb.FindWorkspaceRequest{Name: "fake"}
	wkspResponse, e := workspaceClient.Find(ctx, &wkscpFindReq)
	if e != nil {
		log.Fatalf("could not find workspace: %v", e)
	}
	log.Printf("Workspace find: %v", wkspResponse)
	log.Printf("Workspace find count: %v", wkspResponse.TotalCount)

	// Try to delete the workspace
	workspaceRequest := pb.WorkspaceIdRequest{Id: workspaceResponse.GetId()}
	_, e = workspaceClient.Delete(ctx, &workspaceRequest)
	if e != nil {
		log.Fatalf("Could not delete the workspace (%v)", e)
	}

	// change org status
	orgStatClient := pb.NewOrganizationStatusClient(conn)
	orgStatReq := pb.OrganizationStatusRequest{
		Status:         "SUS",
		OrganizationId: orgData.GetId(),
		CreatedBy:      "pgrubick",
	}
	orgStatResp, e := orgStatClient.Change(ctx, &orgStatReq)
	if e != nil {
		log.Fatalf("could not get organization status histories: %v", e)
	}
	log.Printf("Newest organization status : %v", orgStatResp)

	// get org status histories
	orgStatIdReq := pb.OrganizationIdRequest{Id: orgData.GetId()}
	orgStatIdResp, e := orgStatClient.GetStatuses(ctx, &orgStatIdReq)
	if e != nil {
		log.Fatalf("could not get organization status histories: %v", e)
	}
	log.Printf("Organization status histories: %v", orgStatIdResp)

	userClient := pb.NewUserClient(conn)
	userCreateRequest := pb.UserData{
		FirstName:      "Intel",
		SecondName:     "Sarariman",
		Email:          "example@intel.com",
		Country:        "PL",
		ExternalId:     "123",
		Status:         "CRT",
		OrganizationId: orgData.GetId(),
	}
	userCreateResp, e := userClient.Create(ctx, &userCreateRequest)
	if e != nil {
		log.Fatalf("could not get the user: %v", e)
	}
	log.Printf("User create data (%v)", userCreateResp)

	userRequest := pb.UserIdRequest{UserId: userCreateResp.Id, OrganizationId: orgData.GetId()}
	userResp, e := userClient.GetById(ctx, &userRequest)
	if e != nil {
		log.Fatalf("could not get the user: %v", e)
	}
	log.Printf("User get by id data (%v)", userResp)

	userModifyRequest := pb.UserData{
		Id:                 userResp.Id,
		FirstName:          "NewUserName",
		SecondName:         "NewSecondName",
		Email:              "newemail@example.com",
		ExternalId:         "ext-123",
		Country:            "POL",
		Status:             "SSP",
		OrganizationId:     orgData.GetId(),
		OrganizationStatus: userResp.OrganizationStatus,
		ModifiedBy:         "pkawa",
	}
	userModifyResp, e := userClient.Modify(ctx, &userModifyRequest)
	if e != nil {
		log.Fatalf("could not modify the user: %v", e)
	}
	log.Printf("User data after modification (%v)", userModifyResp)

	userFindRequest := pb.FindUserRequest{
		FirstName:      "New",
		OrganizationId: orgData.GetId(),
		Status:         "ACT",
	}
	userFindResp, e := userClient.Find(ctx, &userFindRequest)
	if e != nil {
		log.Fatalf("could not find users: %v", e)
	}
	log.Printf("Find user data (%v)", userFindResp)

	userFindRequest = pb.FindUserRequest{
		ExternalId: userModifyResp.ExternalId,
	}
	userFindResp, e = userClient.Find(ctx, &userFindRequest)
	if e != nil {
		log.Fatalf("could not find users: %v", e)
	}
	log.Printf("Find user data (no org provided) (%v)", userFindResp)

	_, e = userClient.Delete(ctx, &userRequest)
	if e != nil {
		log.Fatalf("could not delete the user: %v", e)
	}
	log.Printf("User %v deleted", userResp.Id)

	// Try to delete the organization
	orgDelRequest := pb.OrganizationIdRequest{Id: orgData.GetId()}
	_, e = orgClient.Delete(ctx, &orgDelRequest)
	if e != nil {
		log.Fatalf("Could not delete the org (%v)", e)
	}
}
