function UserAgentOptions() {
    /** @type {HTMLVideoElement} */
    this.remoteVideo = null;
    /** @type {HTMLVideoElement} */
    this.localVideo = null;
    /** @type {RTCConfiguration} */
    this.pcConfig = {};
    /** @type {boolean} */
    this.shouldOfferAudio = true;
    /** @type {boolean} */
    this.shouldOfferVideo = false;
    /** @type {boolean} */
    this.shouldUseAudio = true;
    /** @type {boolean} */
    this.shouldUseVideo = false;
}

/**
 * @enum UserAgentEvents
 */
const UserAgentEvents = {}

/**
 * @class UserAgent
 */
class UserAgent extends EventTarget {

    /**
     * @param {UserAgentOptions} options
     */
    constructor(options) {
        super();

        /**
         * @type {UA}
         * @property
         * @private
         */
        this.ua = null;
        const configuration = {
            user_agent: "",
            sockets: [socket],
            uri: "sip:" + username + "@" + host,
            authorization_jwt: jwtToken,
            register: true,
            register_expires: 600,
            // contact_uri: `sip:${username}@${deviceId}.invalid;transport=ws`,
            instance_id: `uuid:${deviceId}`,
        };

        // noinspection JSValidateTypes
        this.ua = new JsSIP.UA(configuration);

        /** @type {RTCSession} */
        this.session = null;

        /** @type {HTMLVideoElement} */
        this.remoteVideo = options.remoteVideo;

        /** @type {HTMLVideoElement} */
        this.localVideo = options.localVideo;

        /** @type {MediaStream} */
        this.localStream = new MediaStream();
        this.localVideo.srcObject = this.localStream;

        /** @type {RTCConfiguration} */
        this.pcConfig = options.pcConfig || {};

        /** @type {boolean} */
        this.shouldOfferAudio = options.shouldOfferAudio;

        /** @type {boolean} */
        this.shouldOfferVideo = options.shouldOfferVideo;

        /** @type {boolean} */
        this.shouldUseAudio = options.shouldUseAudio;

        /** @type {boolean} */
        this.shouldUseVideo = options.shouldUseVideo;
    }


    /**
     * @param {RTCSession} session
     * @private
     */
    setSession(session) {

        this.session = session;
        this.dispatchEvent(new CustomEvent("call.new", { detail: { "session": session }}));

        session.on("icecandidate", (e) => {
            e.ready();
            console.log(`icecandidate`, e.candidate);
        });

        // Fired after the local media stream is added into RTCSession
        // and before the ICE gathering starts for initial INVITE request or “200 OK” response transmission.
        session.on("connecting", ({ request }) => {
            console.log(`session connecting`, request);
        });

        // Fired when receiving or generating a 1XX SIP class response (>100) to the INVITE request.
        session.on("sending", (event) => {
            console.log(`session sending`, event);
        });

        // Fired when receiving or generating a 1XX SIP class response (>100) to the INVITE request.
        session.on("progress", (event) => {
            console.log(`session progress`, event);
        });

        // Fired when the call is accepted (2XX received/sent).
        session.on("accepted", ({ originator, response }) => {
            console.log(`session accepted`, originator, response);
            this.dispatchEvent(new CustomEvent("call.accepted"));
        });

        // Fired when the call is confirmed (ACK received/sent).
        session.on("confirmed", ({ originator, response }) => {
            console.log(`session confirmed`, originator, response);
        });

        // Fired when an established call ends.
        session.on("ended",
            ({ originator, message, cause }) => {
                console.log("session ended", originator, message, cause);
                this.clearSession();
                this.dispatchEvent(new CustomEvent("call.ended"));
            });

        // Fired when an established call ends.
        session.on("sdp",
            (event) => {
                console.log("session sdp", event);
                if ( session.direction === "outgoing" ){
                    if ( event.originator === "remote" && event.type === "answer" ){
                        this.audioPlayer.play(AudioPlayerSounds.Ringback);
                    }
                }
            });

        // Fired when the session was unable to establish.
        session.on("failed", ({ originator, message, cause }) => {
            console.log("session failed", originator, message, cause);
            this.clearSession();
            this.dispatchEvent(new CustomEvent("call.failed"));
        });

        session.on("reinvite", (event) => {
            console.log("reinvite received", event.request);
        });
    }

    attachRemoteStream(stream) {
        this.remoteVideo.srcObject = stream;
    }

    call(uri, extraHeaders = []) {
        const options = {
            pcConfig: this.pcConfig || { iceServers: [] },
            mediaConstraints: {
                audio: this.shouldUseAudio,
                video: this.shouldUseVideo
            },
            rtcOfferConstraints: {
                offerToReceiveAudio: this.shouldOfferAudio,
                offerToReceiveVideo: this.shouldOfferVideo
            },
            extraHeaders: extraHeaders
        }

        const session = this.call(uri, options);
        this.setSession(session);
        session.connection.addEventListener('addstream', (e) => {
                console.log(`addstream called on peer connection`, e);
                this.attachRemoteStream(e.stream);
            });
    }

    clearSession() {
        this.session = null;
    }

}
