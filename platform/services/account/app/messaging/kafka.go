// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package messaging

import (
	"account_service/app/config"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"strings"

	"github.com/IBM/sarama"
	"github.com/xdg-go/scram"
)

type XDGSCRAMClient struct {
	*scram.Client
	*scram.ClientConversation
	scram.HashGeneratorFcn
}

func (x *XDGSCRAMClient) Begin(userName, password, authzID string) (err error) {
	x.Client, err = x.HashGeneratorFcn.NewClient(userName, password, authzID)
	if err != nil {
		return err
	}
	x.ClientConversation = x.Client.NewConversation()
	return nil
}

func (x *XDGSCRAMClient) Step(challenge string) (response string, err error) {
	response, err = x.ClientConversation.Step(challenge)
	return
}

func (x *XDGSCRAMClient) Done() bool {
	return x.ClientConversation.Done()
}

func newProducer() (sarama.SyncProducer, error) {
	producerConfig := sarama.NewConfig()
	producerConfig.Producer.Return.Successes = true
	producerConfig.Producer.RequiredAcks = sarama.WaitForAll
	producerConfig.Producer.Retry.Max = 5
	producerConfig.Net.SASL.Enable = true
	if config.KafkaUsername == "" || config.KafkaPassword == "" {
		producerConfig.Net.SASL.Enable = false
	}

	producerConfig.Net.SASL.User = config.KafkaUsername
	producerConfig.Net.SASL.Password = config.KafkaPassword
	producerConfig.Net.SASL.Mechanism = sarama.SASLTypeSCRAMSHA512
	producerConfig.Net.SASL.SCRAMClientGeneratorFunc = func() sarama.SCRAMClient { return &XDGSCRAMClient{HashGeneratorFcn: scram.SHA512} }

	if config.KafkaSecurityProtocol == "SASL_SSL" {
		systemCertPool, err := x509.SystemCertPool()
		if err != nil {
			return nil, err
		}

		tlsConfig := tls.Config{}
		tlsConfig.RootCAs = systemCertPool

		producerConfig.Net.TLS.Enable = true
		producerConfig.Net.TLS.Config = &tlsConfig
	}

	conn, err := sarama.NewSyncProducer(strings.Split(config.KafkaAddress, ","), producerConfig)
	if err != nil {
		return nil, err
	}
	return conn, nil
}

func SendMessage(topic string, message []byte) error {
	producer, err := newProducer()
	if err != nil {
		return err
	}

	defer func(producer sarama.SyncProducer) {
		err := producer.Close()
		if err != nil {
			fmt.Printf("error closing sarama sync producer: %v", err)
		}
	}(producer)

	msg := &sarama.ProducerMessage{
		Topic: topic,
		Value: sarama.StringEncoder(message),
	}
	_, _, err = producer.SendMessage(msg)
	if err != nil {
		return err
	}
	return nil
}
