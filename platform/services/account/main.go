// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package main

import (
	"context"
	"database/sql"
	"fmt"
	"net"
	"net/http"
	"time"

	"account_service/app/common/utils"
	"account_service/app/config"
	"account_service/app/grpc/membership"
	user_status "account_service/app/grpc/membership_status"
	"account_service/app/grpc/organization"
	"account_service/app/grpc/organization_status"
	"account_service/app/grpc/personal_access_token"
	"account_service/app/grpc/user"
	"account_service/app/grpc/user_settings"
	"account_service/app/grpc/workspace"
	"account_service/app/grpc_gateway"
	"account_service/app/models"
	"account_service/app/repository"
	"account_service/app/rest"
	"account_service/app/roles"
	membershipSvc "account_service/app/services/membership"
	orgSvc "account_service/app/services/organization"
	roleSvc "account_service/app/services/role"
	usersSvc "account_service/app/services/user"
	workspaceSvc "account_service/app/services/workspace"
	"account_service/app/telemetry"

	"geti.com/account_service_grpc/pb"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	_ "go.uber.org/automaxprocs" // Required to prevent CPU throttling in k8s
	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var (
	logger = utils.InitializeLogger()
)

func runGRPCServer(db *gorm.DB) {
	lis, err := net.Listen("tcp", config.GrpcServerAddress)
	if err != nil {
		logger.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()

	orgStatusServer := organization_status.GRPCServer{DB: db}
	pb.RegisterOrganizationStatusServer(s, &orgStatusServer)
	workspaceServer := workspace.GRPCServer{DB: db}
	pb.RegisterWorkspaceServer(s, &workspaceServer)
	workspaceService := workspaceSvc.Service{DB: db}
	userRepository := repository.NewUserRepository(db)
	userService := usersSvc.NewuserService(userRepository)
	userServer := user.GRPCServer{DB: db, WorkspaceService: &workspaceService, Service: userService}
	pb.RegisterUserServer(s, &userServer)
	userStatusServer := user_status.GRPCServer{DB: db}
	pb.RegisterUserStatusServer(s, &userStatusServer)
	membershipRepository := repository.NewMembershipRepository(db)
	organizationRepository := repository.NewOrganizationRepository(db)
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Fatalf("unable to initialize client: %v", err)
	}
	roleService := roleSvc.NewService(rolesMgr)
	patRepository := repository.NewPersonalAccessTokenRepository(db)
	organizationService := orgSvc.NewOrganizationRepository(organizationRepository, roleService)
	membershipService := membershipSvc.NewMembershipService(membershipRepository, patRepository, organizationService, roleService)
	membershipServer := membership.GRPCServer{Service: membershipService}
	orgService := orgSvc.Service{DB: db}
	orgServer := organization.GRPCServer{DB: db, OrganizationService: orgService, MembershipService: membershipService}
	pb.RegisterOrganizationServer(s, &orgServer)
	pb.RegisterMembershipServer(s, &membershipServer)
	userSettingsServer := user_settings.GRPCServer{DB: db}
	pb.RegisterUserSettingsServiceServer(s, &userSettingsServer)
	patServer := personal_access_token.GRPCServer{DB: db}
	pb.RegisterPersonalAccessTokenServer(s, &patServer)

	logger.Infof("grpc server listening at %v", lis.Addr())
	err = s.Serve(lis)
	if err != nil {
		logger.Fatalf("failed to serve: %v", err)
	}
}

func runGRPCGatewayServer() {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	mux := runtime.NewServeMux(
		runtime.WithIncomingHeaderMatcher(grpc_gateway.HTTPRequestHeadersMatcher),
		runtime.WithForwardResponseOption(grpc_gateway.HTTPResponseModifier),
	)

	err := mux.HandlePath("POST", "/api/v1/organizations/{id}/photos", rest.HandleOrganizationAddPhoto)
	if err != nil {
		logger.Fatalf("failed to register POST /organizations/{id}/photos custom rest handler for GRPC Gateway: %v", err)
	}

	err = mux.HandlePath("POST", "/api/v1/organizations/{organization_id}/users/{user_id}/photos", rest.HandleUserAddPhoto)
	if err != nil {
		logger.Fatalf("failed to register POST /organizations/{organization_id}/users/{user_id}/photos custom rest handler for GRPC Gateway: %v", err)
	}

	err = mux.HandlePath("POST", "/api/v1/logout", rest.HandleLogout)
	if err != nil {
		logger.Fatalf("failed to register POST /logout custom rest handler for GRPC Gateway: %v", err)
	}

	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}

	err = pb.RegisterOrganizationHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register organization handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterWorkspaceHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register workspace handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterUserHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register user handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterUserStatusHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register user handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterUserSettingsServiceHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register user handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterMembershipHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register membership handler for GRPC Gateway: %v", err)
	}

	err = pb.RegisterPersonalAccessTokenHandlerFromEndpoint(ctx, mux, config.GrpcServerAddress, opts)
	if err != nil {
		logger.Fatalf("failed to register personal access token for GRPC Gateway: %v", err)
	}

	logger.Infof("grpc gateway server listening at %v", config.GRPCGatewayServerAddress)
	err = http.ListenAndServe(config.GRPCGatewayServerAddress, mux)
	if err != nil {
		logger.Fatalf("failed to run GRPC Gateway Server: %v", err)
	}
}

func initDB() *gorm.DB {
	dsn := fmt.Sprintf("host=%v user=%v password=%v dbname=%v port=%v sslmode=%v",
		config.DBHost, config.DBUser, config.DBPassword, config.DBDatabaseName, config.DBPort, config.DBSSLMode)

	if config.DBSSLRootCert != "" {
		dsn = fmt.Sprintf("%v sslrootcert=%v", dsn, config.DBSSLRootCert)
	}

	gormConfiguration := gorm.Config{
		NowFunc: func() time.Time {
			nowTime := time.Now().Local()
			nowTimeSecondRounded := nowTime.Round(time.Second)
			return nowTimeSecondRounded
		},
	}

	db, err := gorm.Open(postgres.Open(dsn), &gormConfiguration)
	if err != nil {
		logger.Fatalf("failed to open connection to db: %v", err)
	}

	org := models.Organization{}
	orgStatusHistory := models.OrganizationStatusHistory{}
	worksp := models.Workspace{}
	userModel := models.User{}
	userStatusModel := models.UserStatus{}
	pat := models.PersonalAccessToken{}
	userSettings := models.UserSettings{}

	err = db.AutoMigrate(&org, &orgStatusHistory, &worksp, &userModel, &userStatusModel, &pat, &userSettings)
	if err != nil {
		logger.Fatalf("failed to migrate db: %v", err)
	}

	usersOldUniqueEmailConstraintName := "users_email_key"
	if db.Migrator().HasConstraint(&userModel, usersOldUniqueEmailConstraintName) {
		err := db.Migrator().DropConstraint(&userModel, usersOldUniqueEmailConstraintName)
		if err != nil {
			logger.Errorf("failed to delete %v constraint from users table", usersOldUniqueEmailConstraintName)
		}
	}

	return db
}

func initSpiceDB() {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Fatalf("unable to initialize client: %v", err)
	}

	err = rolesMgr.DeleteUserDirectory()
	if err != nil {
		logger.Errorf("unable to migrate user_directory: %v", err)
	}

	err = rolesMgr.WriteSchema()
	if err != nil {
		logger.Fatalf("unable to initialize schema: %v", err)
	}
}

func initMetrics(db *gorm.DB) {
	telemetry.InitMeter()
	telemetry.InitGauges()
	telemetry.RegisterMetricsCallback(db)
}

func main() {
	defer func(logger *zap.SugaredLogger) {
		err := logger.Sync()
		if err != nil {
			fmt.Printf("error closing logger: %v", err)
		}
	}(logger)
	logger.Info("starting app...")

	db := initDB()
	conn, err := db.DB()
	if err != nil {
		logger.Fatalf("error getting db connection: %v", err)
	}
	defer func(conn *sql.DB) {
		err := conn.Close()
		if err != nil {
			fmt.Printf("error closing db connection: %v", err)
		}
	}(conn)

	initSpiceDB()

	go runGRPCServer(db)
	if config.OtelEnableMetrics {
		logger.Info("Enabling metrics reporting")
		initMetrics(db)
	} else {
		logger.Warn("Metrics reporting disabled. To enable it, deploy account service with ENABLE_METRICS env variable set to true.")
	}
	runGRPCGatewayServer()
}
