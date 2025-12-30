package com.panda.order_producer.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.panda.order_producer.model.OrderCreated;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
@Slf4j
@RequiredArgsConstructor
public class OrderProducer {
    private static final String TOPIC = "order-created";

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    /**
     * Sends an OrderCreated event to Kafka.
     *
     * @param order the order event to send
     * @throws JsonProcessingException if serialization fails
     */
    public void sendOrderCreatedEvent(OrderCreated order) throws JsonProcessingException {
        String orderId = order.getOrderId();
        String orderJson = objectMapper.writeValueAsString(order);

        log.info("Sending order event - orderId: {}", orderId);
        CompletableFuture<SendResult<String, String>> future = kafkaTemplate.send(TOPIC, orderId, orderJson);

        future.whenComplete((result, ex) -> {
            if (ex == null) {
                log.info("Order sent successfully - orderId: {}, partition: {}, offset: {}",
                        orderId,
                        result.getRecordMetadata().partition(),
                        result.getRecordMetadata().partition()
                );
            }
            else {
                log.error("Failed to send order - orderId: {}, error: {}", orderId, ex.getMessage());
            }
        });
    }
}
