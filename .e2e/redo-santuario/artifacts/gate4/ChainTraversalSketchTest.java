/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.xml.security.test.dom.keys.keyresolver;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.cert.X509Certificate;

import javax.crypto.SecretKey;

import org.apache.xml.security.Init;
import org.apache.xml.security.keys.KeyInfo;
import org.apache.xml.security.keys.keyresolver.KeyResolver;
import org.apache.xml.security.keys.keyresolver.KeyResolverException;
import org.apache.xml.security.keys.keyresolver.KeyResolverSpi;
import org.apache.xml.security.keys.storage.StorageResolver;
import org.apache.xml.security.test.dom.TestUtils;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class ChainTraversalSketchTest {

    private static PublicKey expectedKey;
    private static Element unresolvedElement;

    private static final Declining controlDeclining = new Declining();
    private static Succeeding controlSucceeding;

    private static final Declining measuredDeclining = new Declining();
    private static final AcceptingThenRejecting measuredRejecting = new AcceptingThenRejecting();
    private static Succeeding measuredSucceeding;
    private static boolean measuredChainInstalled;

    @BeforeAll
    static void setUpClass() throws Exception {
        Init.init();

        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        expectedKey = generator.generateKeyPair().getPublic();
        controlSucceeding = new Succeeding(expectedKey);
        measuredSucceeding = new Succeeding(expectedKey);

        Document document = TestUtils.newDocument();
        unresolvedElement = document.createElementNS("urn:chain-traversal-sketch", "sketch:Material");
        document.appendChild(unresolvedElement);
    }

    @Test
    @Order(1)
    void successfulDefaultKeyValueResolutionIsUnchanged() throws Exception {
        Document document = TestUtils.newDocument();
        KeyInfo keyInfo = new KeyInfo(document);
        keyInfo.addKeyValue(expectedKey);

        assertEquals(expectedKey, keyInfo.getPublicKey());
    }

    @Test
    @Order(2)
    void declineContinuesTheScan() throws Exception {
        // Registration at the start reverses insertion order.
        KeyResolver.register(controlSucceeding, true);
        KeyResolver.register(controlDeclining, true);

        PublicKey resolved = KeyResolver.getPublicKey(unresolvedElement, null, null, false);

        assertSame(expectedKey, resolved);
        assertEquals(1, controlDeclining.invocations());
    }

    @Test
    @Order(3)
    void acceptingThenRejectingOutcomeIsFailure() {
        installMeasuredChain();
        resetMeasuredInvocations();

        assertThrows(
            KeyResolverException.class,
            () -> KeyResolver.getPublicKey(unresolvedElement, null, null, false),
            "an accepting resolver that rejects its material must make resolution fail"
        );
    }

    @Test
    @Order(4)
    void acceptingThenRejectingDoesNotConsultLaterResolver() throws Exception {
        installMeasuredChain();
        resetMeasuredInvocations();

        try {
            KeyResolver.getPublicKey(unresolvedElement, null, null, false);
        } catch (KeyResolverException expected) {
            // Total failure is the required outcome; this assertion measures traversal only.
        }

        assertEquals(
            0,
            measuredSucceeding.invocations(),
            "a resolver after an accepting rejection must not be consulted"
        );
    }

    @Test
    @Order(5)
    void terminalNamesConsultedResolversInOrder() {
        installMeasuredChain();
        resetMeasuredInvocations();

        KeyResolverException failure = assertThrows(
            KeyResolverException.class,
            () -> KeyResolver.getPublicKey(unresolvedElement, null, null, false)
        );
        String rendered = render(failure);
        int declining = rendered.indexOf(Declining.class.getSimpleName());
        int rejecting = rendered.indexOf(AcceptingThenRejecting.class.getSimpleName());

        assertTrue(declining >= 0, () -> "missing declining resolver in: " + rendered);
        assertTrue(rejecting > declining, () -> "resolver outcomes are missing or out of order in: " + rendered);
        assertFalse(
            rendered.contains(Succeeding.class.getSimpleName()),
            () -> "unconsulted succeeding resolver was reported in: " + rendered
        );
    }

    private static void installMeasuredChain() {
        if (!measuredChainInstalled) {
            // Add at the front in reverse so these three precede both controls and defaults.
            KeyResolver.register(measuredSucceeding, true);
            KeyResolver.register(measuredRejecting, true);
            KeyResolver.register(measuredDeclining, true);
            measuredChainInstalled = true;
        }
    }

    private static void resetMeasuredInvocations() {
        measuredDeclining.reset();
        measuredRejecting.reset();
        measuredSucceeding.reset();
    }

    private static String render(Throwable failure) {
        StringWriter rendered = new StringWriter();
        failure.printStackTrace(new PrintWriter(rendered));
        return rendered.toString();
    }

    public static class Declining extends KeyResolverSpi {

        private int invocations;

        public int invocations() {
            return invocations;
        }

        public void reset() {
            invocations = 0;
        }

        @Override
        protected boolean engineCanResolve(Element element, String baseURI, StorageResolver storage) {
            invocations++;
            return false;
        }

        @Override
        protected PublicKey engineResolvePublicKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected X509Certificate engineResolveX509Certificate(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected SecretKey engineResolveSecretKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected PrivateKey engineResolvePrivateKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }
    }

    public static class AcceptingThenRejecting extends KeyResolverSpi {

        private int invocations;

        public int invocations() {
            return invocations;
        }

        public void reset() {
            invocations = 0;
        }

        @Override
        protected boolean engineCanResolve(Element element, String baseURI, StorageResolver storage) {
            invocations++;
            return true;
        }

        @Override
        protected PublicKey engineResolvePublicKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected X509Certificate engineResolveX509Certificate(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected SecretKey engineResolveSecretKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected PrivateKey engineResolvePrivateKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }
    }

    public static class Succeeding extends KeyResolverSpi {

        private final PublicKey publicKey;
        private int invocations;

        public Succeeding(PublicKey publicKey) {
            this.publicKey = publicKey;
        }

        public int invocations() {
            return invocations;
        }

        public void reset() {
            invocations = 0;
        }

        @Override
        protected boolean engineCanResolve(Element element, String baseURI, StorageResolver storage) {
            invocations++;
            return true;
        }

        @Override
        protected PublicKey engineResolvePublicKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return publicKey;
        }

        @Override
        protected X509Certificate engineResolveX509Certificate(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected SecretKey engineResolveSecretKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }

        @Override
        protected PrivateKey engineResolvePrivateKey(
            Element element, String baseURI, StorageResolver storage, boolean secureValidation
        ) {
            return null;
        }
    }
}
